"""
Canonical section vocabulary. Maps a schema-relevant "canonical key" to the
various real-world heading strings people use for it.

Two tiers, both matched the same way (fuzzy, case-insensitive):
- SECTION_ALIASES: canonical keys that map to an actual PortfolioData field
  (or, for "contact", is handled separately -- see section_classifier.py).
- UNSUPPORTED_ALIASES: canonical keys we recognize (so they get a clean
  label) but that don't have a dedicated schema field. Their content is
  routed to `uncategorized[canonical_key]` instead of being dropped or
  dumped under raw, messy heading text.

Anything matching NEITHER dict falls through to `uncategorized[raw_heading]`.
"""

SECTION_ALIASES: dict[str, list[str]] = {
    "contact": ["contact info", "contact information", "contact"],
    "summary": ["summary", "objective", "profile", "my journey", "about me"],
    "skills": ["skills", "technical skills", "core competencies", "toolbox"],
    "education": ["education", "academic background"],
    "experience": [
        "experience", "work experience", "internship experience",
        "employment", "internship", "where i've worked",
        "freelance work", "freelance", "contract work",
    ],
    "projects": [
        "projects", "personal projects", "portfolio", "what i've built",
    ],
    "certifications": ["certifications", "certificates", "licenses", "learning"],
    "achievements": ["achievements", "awards", "honors"],
}

# Recognized, but no dedicated PortfolioData field for these (yet).
# Routed to uncategorized[canonical_key] rather than dropped.
UNSUPPORTED_ALIASES: dict[str, list[str]] = {
    "soft_skills": ["soft skills"],
    "languages_known": ["languages known", "spoken languages"],
    "competitive_programming": ["competitive programming", "coding profiles"],
    "publications": ["publications", "research"],
    "extracurricular": ["extracurricular activities", "leadership", "activities"],
    "volunteer": ["volunteer work", "social work", "community service"],
    "workshops": ["workshops", "trainings attended", "training"],
    "hobbies": ["hobbies", "interests"],
    "references": ["references"],
}