"""
Turns classified RawBlock groups into typed schema objects.

Entry-splitting fallback (experience/projects/certifications each contain
MULTIPLE entries within one section): the block stream within a section
alternates between "header lines" (title, company, dates -- not bulleted)
and "bullet lines" (the is_bullet flag set by the extractors). We treat a
run of header lines followed by bullets as ONE entry; a header line
appearing again right after bullets have started signals a NEW entry.

Real portfolio docs use two different shapes for lists of entries, and
both are handled:
  1. Header line + sub-bullets ("Campus Calculator" / "- Built a...")
  2. Flat bulleted list, one entry per bullet ("- Project A" / "- Project B")
     with no separate header/description line at all.

If neither shape resolves cleanly (e.g. no bullets at all and no header
repetition to split on), the fallback is to treat the whole section as a
SINGLE entry and attach a ParseWarning rather than guessing wrong or
raising. "Keep content, flag warning, never raise."
"""

import re

from services.parser.blocks import RawBlock
from shared.schemas.portfolio import (
    ContactInfo,
    ExperienceEntry,
    ProjectEntry,
    CertificationEntry,
    EducationEntry,
    Bullet,
    ParseWarning,
)

try:
    import spacy
    _NLP = spacy.load("en_core_web_sm")
except Exception:
    _NLP = None  # NER becomes a no-op; regex-only fallback still works

EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(\+?\d[\d\-\s()]{7,}\d)")
LINKEDIN_RE = re.compile(r"(linkedin\.com/\S+)", re.IGNORECASE)
GITHUB_RE = re.compile(r"(github\.com/\S+)", re.IGNORECASE)
DATE_RANGE_RE = re.compile(
    r"([A-Za-z]{3,9}\s+\d{4}|\d{4})\s*[-\u2013\u2014]\s*(Present|present|[A-Za-z]{3,9}\s+\d{4}|\d{4})"
)
_TRAILING_YEAR_RE = re.compile(r"\(\s*(19|20)\d{2}\s*\)\s*$")
FREELANCE_HINTS = ("freelance", "contract")
INTERNSHIP_HINTS = ("intern",)


def _strip_bullet_prefix(text: str) -> str:
    return re.sub(r"^[-\u2022*]\s*", "", text).strip()


def extract_contact(blocks: list[RawBlock]) -> ContactInfo:
    """
    Name = first non-empty line of the whole document (heuristic).
    Everything else pulled by regex from the first ~15 lines, since contact
    info is always near the top and rarely appears elsewhere.
    """
    head_text = " \n".join(b.text for b in blocks[:15])
    name = blocks[0].text.strip() if blocks else "Unknown"

    email_match = EMAIL_RE.search(head_text)
    phone_match = PHONE_RE.search(head_text)
    linkedin_match = LINKEDIN_RE.search(head_text)
    github_match = GITHUB_RE.search(head_text)

    location = None
    loc_line = next((b.text for b in blocks[:15] if "location" in b.text.lower()), None)
    if loc_line:
        location = loc_line.split(":", 1)[-1].strip()

    return ContactInfo(
        name=name,
        email=email_match.group(0) if email_match else None,
        phone=phone_match.group(0).strip() if phone_match else None,
        location=location,
        linkedin=linkedin_match.group(0) if linkedin_match else None,
        github=github_match.group(0) if github_match else None,
    )


def extract_summary(blocks: list[RawBlock]) -> str | None:
    if not blocks:
        return None
    return " ".join(b.text for b in blocks).strip() or None


def extract_skills(blocks: list[RawBlock]) -> list[str]:
    """Split on commas/bullets/newlines, normalize casing, dedupe."""
    raw = " ".join(_strip_bullet_prefix(b.text) for b in blocks)
    parts = re.split(r"[,\n\u2022]", raw)
    seen, result = set(), []
    for p in parts:
        cleaned = p.strip().rstrip(".")
        if cleaned and cleaned.lower() not in seen:
            seen.add(cleaned.lower())
            result.append(cleaned)
    return result


def extract_achievements(blocks: list[RawBlock]) -> list[str]:
    return [_strip_bullet_prefix(b.text) for b in blocks if b.text.strip()]




def _split_into_entries(blocks: list[RawBlock]) -> list[list[RawBlock]]:
    """
    A header (non-bullet) line starts a NEW entry if any of:
      - a bullet has already been seen in the current entry (original rule)
      - it was preceded by a blank line in the source document
      - it's the first content block after a NEW heading was detected
        (even one mapping to the same canonical section as before --
        e.g. "Freelance Work" following "Internship Experience")
      - a date-range line has already been seen in the current entry, and
        this line is NOT itself a date range -- i.e. "Title / Date range /
        NEXT Title" is recognized as a new entry starting at "NEXT Title"

    Special cases (checked before the state machine, since both mean
    "every block is independently its own complete entry"):
      - EVERY block is a bullet (flat list: "- Project A" / "- Project B")
      - EVERY block ends in a trailing "(YYYY)" year, e.g. "Name (2024)"
        one-liners with no bullets, blanks, or date-ranges separating them
        -- each such self-contained line becomes its own entry.

    Falls back to "everything is one entry" if nothing above ever fires.
    """
    if not blocks:
        return []

    if all(b.is_bullet for b in blocks):
        return [[b] for b in blocks]

    if all(_TRAILING_YEAR_RE.search(b.text) for b in blocks):
        return [[b] for b in blocks]

    entries: list[list[RawBlock]] = []
    current: list[RawBlock] = []
    seen_bullet_in_current = False
    seen_date_in_current = False

    for block in blocks:
        if block.is_bullet:
            current.append(block)
            seen_bullet_in_current = True
            continue

        is_date_line = bool(DATE_RANGE_RE.search(block.text))

        starts_new_entry = current and (
            seen_bullet_in_current
            or block.blank_before
            or block.section_boundary
            or (seen_date_in_current and not is_date_line)
        )

        if starts_new_entry:
            entries.append(current)
            current = [block]
            seen_bullet_in_current = False
            seen_date_in_current = is_date_line
        else:
            current.append(block)
            if is_date_line:
                seen_date_in_current = True

    if current:
        entries.append(current)

    return entries if entries else [blocks]


def _guess_employment_type(header_text: str) -> str | None:
    lowered = header_text.lower()
    if any(h in lowered for h in FREELANCE_HINTS):
        return "freelance"
    if any(h in lowered for h in INTERNSHIP_HINTS):
        return "internship"
    return "full_time"


def extract_experience(
    blocks: list[RawBlock],
) -> tuple[list[ExperienceEntry], list[ParseWarning]]:
    warnings: list[ParseWarning] = []
    entries_raw = _split_into_entries(blocks)

    if len(entries_raw) == 1 and len(blocks) > 6:
        warnings.append(
            ParseWarning(
                section="experience",
                message="Could not confidently separate multiple entries; treated as one.",
                severity="warn",
            )
        )

    results: list[ExperienceEntry] = []
    for entry_blocks in entries_raw:
        header_lines = [b for b in entry_blocks if not b.is_bullet]
        bullet_lines = [b for b in entry_blocks if b.is_bullet]
        header_text = " ".join(b.text for b in header_lines)

        date_match = DATE_RANGE_RE.search(header_text)
        start_date, end_date, is_current = None, None, False
        if date_match:
            start_date = date_match.group(1)
            end_date = date_match.group(2)
            if end_date.lower() == "present":
                is_current = True
                end_date = None

        # Title/company: first header line, split on " - " if present.
        title, company = None, None
        title_line = header_lines[0].text if header_lines else ""
        title_line_no_dates = DATE_RANGE_RE.sub("", title_line).strip(" -")
        if " - " in title_line_no_dates:
            title, company = [s.strip() for s in title_line_no_dates.split(" - ", 1)]
        elif title_line_no_dates:
            title = title_line_no_dates

        if title is None and company is None:
            warnings.append(
                ParseWarning(
                    section="experience",
                    message="Could not identify a title/company for one entry.",
                    severity="warn",
                )
            )

        location = None
        if _NLP is not None and title_line_no_dates:
            doc = _NLP(title_line_no_dates)
            gpe = [ent.text for ent in doc.ents if ent.label_ == "GPE"]
            if gpe:
                location = gpe[0]

        results.append(
            ExperienceEntry(
                company=company,
                title=title,
                employment_type=_guess_employment_type(header_text),
                location=location,
                start_date=start_date,
                end_date=end_date,
                is_current=is_current,
                bullets=[Bullet(text=_strip_bullet_prefix(b.text)) for b in bullet_lines],
            )
        )

    return results, warnings


def extract_projects(blocks: list[RawBlock]) -> list[ProjectEntry]:
    entries_raw = _split_into_entries(blocks)
    results: list[ProjectEntry] = []
    for entry_blocks in entries_raw:
        header_lines = [b for b in entry_blocks if not b.is_bullet]
        bullet_lines = [b for b in entry_blocks if b.is_bullet]

        if not header_lines and len(bullet_lines) == 1:
            # Flat bulleted list case (e.g. "- Project Name" with no
            # separate header/description line) -- the bullet text itself
            # IS the project name.
            name = _strip_bullet_prefix(bullet_lines[0].text)
            results.append(ProjectEntry(name=name, description=None, tech_stack=[], bullets=[]))
            continue

        name = header_lines[0].text.strip() if header_lines else "Untitled Project"
        description = " ".join(b.text for b in header_lines[1:]) or None

        tech_stack: list[str] = []
        tech_match = re.search(r"\(([^)]+)\)", name)
        if tech_match:
            tech_stack = [t.strip() for t in tech_match.group(1).split(",")]
            name = name[: tech_match.start()].strip()

        results.append(
            ProjectEntry(
                name=name,
                description=description,
                tech_stack=tech_stack,
                bullets=[Bullet(text=_strip_bullet_prefix(b.text)) for b in bullet_lines],
            )
        )
    return results


def extract_certifications(blocks: list[RawBlock]) -> list[CertificationEntry]:
    results: list[CertificationEntry] = []
    for b in blocks:
        text = _strip_bullet_prefix(b.text)
        if not text:
            continue
        date_match = DATE_RANGE_RE.search(text) or re.search(r"\b(19|20)\d{2}\b", text)
        date = date_match.group(0) if date_match else None
        text_wo_date = text.replace(date, "").strip(" ,-") if date else text

        if " - " in text_wo_date:
            name, issuer = [s.strip() for s in text_wo_date.split(" - ", 1)]
        elif "," in text_wo_date:
            name, issuer = [s.strip() for s in text_wo_date.split(",", 1)]
        else:
            name, issuer = text_wo_date, None

        results.append(CertificationEntry(name=name, issuer=issuer, date=date))
    return results


def extract_education(blocks: list[RawBlock]) -> list[EducationEntry]:
    entries_raw = _split_into_entries(blocks)
    results: list[EducationEntry] = []
    for entry_blocks in entries_raw:
        lines = [_strip_bullet_prefix(b.text) for b in entry_blocks]
        if not lines:
            continue
        institution = lines[0]
        degree, year, gpa, coursework = None, None, None, []

        rest = " ".join(lines[1:])
        year_match = re.search(r"\b(19|20)\d{2}\b", rest)
        if year_match:
            year = year_match.group(0)

        gpa_match = re.search(r"(CGPA|GPA)\s*[:\-]?\s*([\d.]+)", rest, re.IGNORECASE)
        if gpa_match:
            gpa = gpa_match.group(0)

        for line in lines[1:]:
            if "coursework" in line.lower():
                coursework = [
                    c.strip() for c in line.split(":", 1)[-1].split(",") if c.strip()
                ]
            elif degree is None and "coursework" not in line.lower():
                degree = line

        results.append(
            EducationEntry(
                institution=institution,
                degree=degree,
                year=year,
                gpa_or_percentage=gpa,
                coursework=coursework,
            )
        )
    return results