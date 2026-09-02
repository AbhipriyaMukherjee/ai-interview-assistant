"""
RawBlock: the internal, format-agnostic intermediate representation both
extractors produce. Everything downstream of extraction (section
classification, entity extraction) works ONLY with RawBlock objects and
never needs to know whether the source was a .docx or a .pdf.
"""

from dataclasses import dataclass


@dataclass
class RawBlock:
    text: str
    is_heading: bool = False
    heading_score: int = 0
    is_bullet: bool = False
    order: int = 0  # reading order, for stable re-sorting if ever needed
    blank_before: bool = False  # a blank line / larger-than-normal gap preceded this block
    section_boundary: bool = False  # set by section_classifier: this is the first
                                     # content block right after ANY heading was detected,
                                     # even if that heading maps to the same section key
                                     # as before (e.g. "Freelance Work" following
                                     # "Internship Experience", both -> "experience")