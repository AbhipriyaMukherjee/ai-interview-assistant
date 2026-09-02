"""
Pydantic schema for the output of the Day 2 portfolio parser.

Design principles (locked decisions from planning):
- Everything except `contact.name` is optional. A thin/empty section is a
  valid document shape (e.g. a fresher with zero experience), not an error.
- Every bullet is its own record with a stub `impact_score` field, so Day 6's
  truncation logic has something to sort without a schema migration later.
- `warnings` + `uncategorized` capture parsing uncertainty explicitly rather
  than silently dropping content or raising. The only thing allowed to
  actually fail parsing is a genuinely unreadable file.
"""

from typing import Literal
from pydantic import BaseModel, Field


class ParseWarning(BaseModel):
    section: str
    message: str
    severity: Literal["info", "warn"] = "warn"


class Bullet(BaseModel):
    text: str
    impact_score: float | None = None  # stub -- filled in by Day 6


class ContactInfo(BaseModel):
    name: str
    email: str | None = None
    phone: str | None = None
    location: str | None = None
    linkedin: str | None = None
    github: str | None = None


class ExperienceEntry(BaseModel):
    company: str | None = None
    title: str | None = None
    employment_type: Literal[
        "internship", "full_time", "freelance", "part_time", "other"
    ] | None = None
    location: str | None = None
    start_date: str | None = None  # raw string, e.g. "Jan 2025" -- not parsed
    end_date: str | None = None
    is_current: bool = False
    bullets: list[Bullet] = Field(default_factory=list)


class ProjectEntry(BaseModel):
    name: str
    description: str | None = None
    tech_stack: list[str] = Field(default_factory=list)
    bullets: list[Bullet] = Field(default_factory=list)


class CertificationEntry(BaseModel):
    name: str
    issuer: str | None = None
    date: str | None = None


class EducationEntry(BaseModel):
    institution: str
    degree: str | None = None
    year: str | None = None
    gpa_or_percentage: str | None = None
    coursework: list[str] = Field(default_factory=list)


class PortfolioData(BaseModel):
    contact: ContactInfo
    summary: str | None = None
    skills: list[str] = Field(default_factory=list)
    education: list[EducationEntry] = Field(default_factory=list)
    experience: list[ExperienceEntry] = Field(default_factory=list)
    projects: list[ProjectEntry] = Field(default_factory=list)
    certifications: list[CertificationEntry] = Field(default_factory=list)
    achievements: list[str] = Field(default_factory=list)

    warnings: list[ParseWarning] = Field(default_factory=list)

    # Two kinds of content land here, both non-fatal:
    #  1. Headings that matched NO known alias at all (key = raw heading text)
    #  2. Headings that matched a recognized-but-schema-unsupported category,
    #     e.g. "competitive_programming", "publications", "hobbies"
    #     (key = the canonical category name, cleaner than raw text)
    uncategorized: dict[str, list[str]] = Field(default_factory=dict)