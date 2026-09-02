"""
DOCX extraction: primary signal is python-docx's real paragraph style
metadata (paragraph.style.name starting with "Heading"). This is far more
reliable than PDF's flattened font situation.

FALLBACK: if a document has ZERO paragraphs using Word's actual Heading
styles (very common -- people often just bold text instead of applying a
real style), we fall back to the same gap+keyword heuristic used for PDFs
(services.parser.heuristics), so a casually-formatted DOCX doesn't collapse
into one giant undifferentiated block.

BLANK-LINE SIGNAL: a blank paragraph between two pieces of content is
preserved (rather than discarded) as a structural cue, and is used ONLY for
entry-splitting within a section (see entity_extractor.py) -- never to
promote a line to a whole new top-level section. A short, blank-preceded,
alias-unmatched line is structurally identical whether it's a genuinely new
section or just the next entry's title (e.g. a new project name), so using
it for section-level heading detection produces false positives.

BULLET DETECTION: Word's real "List Bullet" style first; falls back to a
literal "-"/bullet-character text prefix when content was pasted in as
plain text rather than typed and auto-formatted by Word.

A bullet line is NEVER scored as a heading candidate -- a bullet is
definitionally not a section header, regardless of how short it is.
"""

from docx import Document

from services.parser.blocks import RawBlock
from services.parser.aliases import SECTION_ALIASES, UNSUPPORTED_ALIASES
from services.parser import heuristics
from shared.schemas.portfolio import ParseWarning


def _is_bullet_paragraph(paragraph) -> bool:
    if paragraph.style is not None and "List" in paragraph.style.name:
        return True
    return paragraph.text.strip().startswith(("-", "\u2022", "*"))


def _collect_paragraphs_with_blank_flags(doc) -> list[tuple[object, bool]]:
    """
    Returns [(paragraph, blank_before), ...] for every non-empty paragraph,
    where blank_before is True if one or more blank paragraphs immediately
    preceded it in the original document.
    """
    result: list[tuple[object, bool]] = []
    pending_blank = False
    for p in doc.paragraphs:
        if not p.text.strip():
            pending_blank = True
            continue
        result.append((p, pending_blank))
        pending_blank = False
    return result


def extract_blocks(file_path: str) -> tuple[list[RawBlock], list[ParseWarning]]:
    warnings: list[ParseWarning] = []

    try:
        doc = Document(file_path)
    except Exception as exc:
        warnings.append(
            ParseWarning(
                section="document",
                message=f"Could not open DOCX file: {exc}",
                severity="warn",
            )
        )
        return [], warnings

    para_flags = _collect_paragraphs_with_blank_flags(doc)

    if not para_flags:
        warnings.append(
            ParseWarning(
                section="document",
                message="DOCX contained no readable paragraph text.",
                severity="warn",
            )
        )
        return [], warnings

    has_real_heading_styles = any(
        p.style is not None and p.style.name.startswith("Heading")
        for p, _ in para_flags
    )

    blocks: list[RawBlock] = []

    if has_real_heading_styles:
        for i, (p, blank_before) in enumerate(para_flags):
            is_heading = p.style is not None and p.style.name.startswith("Heading")
            is_bullet = _is_bullet_paragraph(p)
            blocks.append(
                RawBlock(
                    text=p.text.strip(),
                    is_heading=is_heading,
                    heading_score=99 if is_heading else 0,  # definitive, not scored
                    is_bullet=is_bullet,
                    order=i,
                    blank_before=blank_before,
                )
            )
    else:
        warnings.append(
            ParseWarning(
                section="document",
                message=(
                    "No native Word Heading styles found -- falling back to "
                    "keyword/formatting/blank-line heuristics for section "
                    "detection."
                ),
                severity="info",
            )
        )
        for i, (p, blank_before) in enumerate(para_flags):
            is_bullet = _is_bullet_paragraph(p)

            if is_bullet:
                blocks.append(
                    RawBlock(
                        text=p.text.strip(),
                        is_heading=False,
                        heading_score=0,
                        is_bullet=True,
                        order=i,
                        blank_before=blank_before,
                    )
                )
                continue

            is_bold = bool(p.runs) and all(
                run.bold for run in p.runs if run.text.strip()
            )
            signals = {"is_bold": is_bold}
            # Note: blank_before is deliberately NOT fed into heading-score
            # here. A blank line before a short, punctuation-free line is
            # structurally identical whether that line is a genuinely new
            # top-level section OR just the next entry's title within the
            # CURRENT section (e.g. a new project name). Without an alias
            # match, these can't be told apart -- so blank_before is used
            # only for entry-splitting (see entity_extractor.py), never for
            # promoting a line to a whole new section.
            score, alias_matched = heuristics.score_heading_candidate(
                p.text, signals, [SECTION_ALIASES, UNSUPPORTED_ALIASES]
            )
            threshold = (
                heuristics.HEADING_SCORE_THRESHOLD
                if alias_matched
                else heuristics.HEADING_SCORE_THRESHOLD_NO_ALIAS
            )
            blocks.append(
                RawBlock(
                    text=p.text.strip(),
                    is_heading=score >= threshold,
                    heading_score=score,
                    is_bullet=False,
                    order=i,
                    blank_before=blank_before,
                )
            )

    return blocks, warnings