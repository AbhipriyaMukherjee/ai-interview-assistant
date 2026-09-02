"""
Shared heading-detection logic, used by BOTH pdf_extractor.py (as its
primary signal, since WPS-exported PDFs flatten font metadata) and
docx_extractor.py (as its FALLBACK, for when a .docx wasn't authored with
real Word "Heading" styles applied).

TWO THRESHOLDS, not one:
- HEADING_SCORE_THRESHOLD applies when the candidate line matches a known
  section alias. Real section headers (even with unconventional wording we
  anticipated in aliases.py) reliably clear this with gap+shortline+
  punctuation+alias-match combined.
- HEADING_SCORE_THRESHOLD_NO_ALIAS applies when NO alias matches. This is
  set deliberately high, because an ordinary entry title (a company name,
  a job title, a project name) sitting after normal resume whitespace looks
  structurally identical to a genuine unrecognized heading -- gap before it,
  short, no trailing punctuation. Confirmed against real fixture data: lines
  like "National University of Technology" or "AI Intern B" score 4 on gap+
  shortline+punctuation alone, which would false-positive as new "sections"
  and rip content out of the correct one. A missed genuinely-novel heading
  just gets misfiled into the current section (recoverable, low-cost); a
  false-positive heading steals legitimate entries away entirely (much more
  damaging). The asymmetry is intentional.
"""

from difflib import SequenceMatcher

HEADING_SCORE_THRESHOLD = 3
HEADING_SCORE_THRESHOLD_NO_ALIAS = 5
MIN_ALIAS_SIMILARITY = 0.75
GAP_RATIO_TRIGGER = 1.15  # gap must be >=15% larger than body-line gap


def _similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def fuzzy_match_alias(
    text: str, alias_dict: dict[str, list[str]]
) -> tuple[str | None, float]:
    """
    Best canonical-key match for `text` against an alias dictionary.
    Returns (canonical_key, similarity) or (None, 0.0) if nothing clears
    MIN_ALIAS_SIMILARITY.
    """
    best_key, best_score = None, 0.0
    cleaned = text.strip().lower()
    for canonical_key, phrases in alias_dict.items():
        for phrase in phrases:
            score = _similarity(cleaned, phrase)
            if score > best_score:
                best_key, best_score = canonical_key, score
    if best_score >= MIN_ALIAS_SIMILARITY:
        return best_key, best_score
    return None, best_score


def score_heading_candidate(
    text: str, signals: dict, alias_dicts: list[dict]
) -> tuple[int, bool]:
    """
    signals may include any of:
      gap_ratio: float   -- line's gap-before divided by the body baseline gap
      font_delta: float  -- this line's font size minus body baseline font size
      is_bold: bool
    alias_dicts: list of alias dictionaries to check against (e.g.
      [SECTION_ALIASES, UNSUPPORTED_ALIASES]).

    Returns (score, alias_matched). Callers should apply
    HEADING_SCORE_THRESHOLD if alias_matched else
    HEADING_SCORE_THRESHOLD_NO_ALIAS -- see module docstring for why.
    """
    score = 0
    text = text.strip()
    if not text:
        return 0, False

    gap_ratio = signals.get("gap_ratio")
    if gap_ratio is not None and gap_ratio > GAP_RATIO_TRIGGER:
        score += 2

    word_count = len(text.split())
    if 1 <= word_count <= 5:
        score += 1

    alias_matched = False
    for alias_dict in alias_dicts:
        _, similarity = fuzzy_match_alias(text, alias_dict)
        if similarity >= MIN_ALIAS_SIMILARITY:
            score += 2
            alias_matched = True
            break

    if not text.endswith((".", ",")):
        score += 1

    font_delta = signals.get("font_delta")
    if font_delta is not None and font_delta > 0.5:
        score += 1

    if signals.get("is_bold"):
        score += 1

    return score, alias_matched