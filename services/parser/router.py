"""
Day 2 entry point. Streamlit calls parse_portfolio() directly (single
process, no internal HTTP -- per the project's locked architecture).

parse_portfolio() raises ONLY if the file is fundamentally unreadable
(corrupt bytes, unsupported extension, zero extractable content). Every
other kind of "missing" or "unusual" input degrades to a ParseWarning
inside a valid PortfolioData -- never a raised exception.
"""

from pathlib import Path

from services.parser import docx_extractor, pdf_extractor, section_classifier, entity_extractor
from shared.schemas.portfolio import PortfolioData, ParseWarning


def parse_portfolio(file_path: str) -> PortfolioData:
    ext = Path(file_path).suffix.lower()

    if ext == ".docx":
        blocks, warnings = docx_extractor.extract_blocks(file_path)
    elif ext == ".pdf":
        blocks, warnings = pdf_extractor.extract_blocks(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}. Only .docx and .pdf are supported.")

    if not blocks:
        raise ValueError(
            "Could not extract any readable content from this file. "
            "It may be corrupt, empty, or a scanned/image-only document."
        )

    contact = entity_extractor.extract_contact(blocks)

    sections, uncategorized, classification_warnings = section_classifier.classify_sections(blocks)
    warnings.extend(classification_warnings)

    summary = entity_extractor.extract_summary(sections.get("summary", []))
    skills = entity_extractor.extract_skills(sections.get("skills", []))
    education = entity_extractor.extract_education(sections.get("education", []))
    achievements = entity_extractor.extract_achievements(sections.get("achievements", []))

    experience, experience_warnings = entity_extractor.extract_experience(
        sections.get("experience", [])
    )
    warnings.extend(experience_warnings)

    projects = entity_extractor.extract_projects(sections.get("projects", []))
    certifications = entity_extractor.extract_certifications(sections.get("certifications", []))

    if not experience:
        warnings.append(
            ParseWarning(
                section="experience",
                message="No experience section found -- treated as an entry-level profile.",
                severity="info",
            )
        )

    return PortfolioData(
        contact=contact,
        summary=summary,
        skills=skills,
        education=education,
        experience=experience,
        projects=projects,
        certifications=certifications,
        achievements=achievements,
        warnings=warnings,
        uncategorized=uncategorized,
    )