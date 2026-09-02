"""
PDF extraction: validated against real WPS-Office-exported fixtures where
ALL font metadata was flattened to Helvetica 10pt (no bold, no size
variation). Font-size/weight heuristics are therefore treated as a bonus
signal only, never a requirement.

Primary signal: vertical whitespace gap analysis. Headings in the tested
fixtures were consistently preceded by a larger gap (~24pt) than the gap
between ordinary body lines (~18pt). Combined with keyword matching against
SECTION_ALIASES via the shared heuristics.score_heading_candidate().

If a page yields effectively no extractable text (scanned/image-only PDF),
we do NOT attempt OCR -- we flag it and return no blocks. See project notes
for the reasoning: OCR solves "no text layer exists", which is a different
failure mode from "styling metadata is flattened", and adding it now would
be solving a problem we haven't actually observed.
"""

import pdfplumber

from services.parser.blocks import RawBlock
from services.parser.aliases import SECTION_ALIASES, UNSUPPORTED_ALIASES
from services.parser import heuristics
from shared.schemas.portfolio import ParseWarning

Y_TOLERANCE = 2.0  # points; chars within this range share a line
MIN_CHARS_PER_PAGE_THRESHOLD = 20  # below this, treat page as image-only


def _group_words_into_lines(words: list[dict]) -> list[dict]:
    """
    words: pdfplumber extract_words() output for one page, already in
    reading order (top-to-bottom, left-to-right).
    Returns one dict per visual line: {text, top, bottom, size, fontname}
    """
    lines: list[dict] = []
    current: list[dict] = []
    current_top: float | None = None

    for w in words:
        if current_top is None or abs(w["top"] - current_top) <= Y_TOLERANCE:
            current.append(w)
            current_top = w["top"] if current_top is None else current_top
        else:
            lines.append(_finalize_line(current))
            current = [w]
            current_top = w["top"]
    if current:
        lines.append(_finalize_line(current))
    return lines


def _finalize_line(words_in_line: list[dict]) -> dict:
    words_in_line.sort(key=lambda w: w["x0"])
    text = " ".join(w["text"] for w in words_in_line)
    sizes = [w.get("size", 0) for w in words_in_line if w.get("size")]
    return {
        "text": text,
        "top": words_in_line[0]["top"],
        "bottom": max(w["bottom"] for w in words_in_line),
        "size": sum(sizes) / len(sizes) if sizes else None,
    }


def extract_blocks(file_path: str) -> tuple[list[RawBlock], list[ParseWarning]]:
    warnings: list[ParseWarning] = []
    all_lines: list[dict] = []

    try:
        with pdfplumber.open(file_path) as pdf:
            total_chars = 0
            for page in pdf.pages:
                words = page.extract_words(extra_attrs=["size", "fontname"])
                total_chars += sum(len(w["text"]) for w in words)
                page_lines = _group_words_into_lines(words)
                all_lines.extend(page_lines)

            if pdf.pages and total_chars < MIN_CHARS_PER_PAGE_THRESHOLD * len(pdf.pages):
                warnings.append(
                    ParseWarning(
                        section="document",
                        message=(
                            "PDF appears to be scanned or image-only -- little "
                            "to no extractable text found. Try re-exporting "
                            "with a text layer, or upload the .docx version."
                        ),
                        severity="warn",
                    )
                )
                return [], warnings

    except Exception as exc:
        warnings.append(
            ParseWarning(
                section="document",
                message=f"Could not open PDF file: {exc}",
                severity="warn",
            )
        )
        return [], warnings

    if not all_lines:
        warnings.append(
            ParseWarning(
                section="document",
                message="No readable lines found in PDF.",
                severity="warn",
            )
        )
        return [], warnings

    # Establish a body-line baseline gap: median gap between consecutive
    # lines. Headings should stand out against this.
    gaps = [
        all_lines[i]["top"] - all_lines[i - 1]["bottom"]
        for i in range(1, len(all_lines))
    ]
    gaps = [g for g in gaps if g > 0]
    body_baseline_gap = sorted(gaps)[len(gaps) // 2] if gaps else 0

    sizes = [l["size"] for l in all_lines if l.get("size")]
    body_baseline_font = sorted(sizes)[len(sizes) // 2] if sizes else None

    blocks: list[RawBlock] = []
    any_heading_scored = False

    for i, line in enumerate(all_lines):
        gap_before = (line["top"] - all_lines[i - 1]["bottom"]) if i > 0 else None
        gap_ratio = (gap_before / body_baseline_gap) if (gap_before and body_baseline_gap) else None
        font_delta = (
            line["size"] - body_baseline_font
            if line.get("size") and body_baseline_font
            else None
        )

        signals = {"gap_ratio": gap_ratio, "font_delta": font_delta}
        score, alias_matched = heuristics.score_heading_candidate(
            line["text"], signals, [SECTION_ALIASES, UNSUPPORTED_ALIASES]
        )
        threshold = (
            heuristics.HEADING_SCORE_THRESHOLD
            if alias_matched
            else heuristics.HEADING_SCORE_THRESHOLD_NO_ALIAS
        )
        is_heading = score >= threshold
        any_heading_scored = any_heading_scored or is_heading


        is_bullet = line["text"].strip().startswith(("-", "\u2022", "*"))

        blocks.append(
            RawBlock(
                text=line["text"].strip(),
                is_heading=is_heading,
                heading_score=score,
                is_bullet=is_bullet,
                order=i,
            )
        )

    if not any_heading_scored:
        warnings.append(
            ParseWarning(
                section="document",
                message=(
                    "No section headings could be confidently detected. "
                    "Document structure may be unusual -- content preserved "
                    "as a single unstructured block."
                ),
                severity="warn",
            )
        )

    return blocks, warnings