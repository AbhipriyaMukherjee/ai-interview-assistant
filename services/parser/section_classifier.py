"""
Walks the flat, ordered list of RawBlocks and groups everything under its
nearest preceding heading. Possible outcomes per heading:

  1. Matches "contact"                   -> silently skipped here; contact
                                             info is extracted separately by
                                             entity_extractor.extract_contact()
                                             via a direct scan of all blocks.
  2. Matches a SECTION_ALIASES key        -> content goes to sections[key]
  3. Matches an UNSUPPORTED_ALIASES key   -> content goes to
                                             uncategorized[canonical_key]
                                             (clean label, no schema field yet)
  4. Matches neither                      -> content goes to
                                             uncategorized[raw_heading_text]
                                             (a warning is also logged)

BOUNDARY MARKING: the first content block after ANY detected heading gets
section_boundary=True, even when that heading maps to the SAME canonical
key as the section already in progress (e.g. "Freelance Work" appearing
after "Internship Experience" -- both map to "experience"). Without this,
entity_extractor's entry-splitting has no way to know a new heading
occurred there at all.

Content appearing BEFORE the first detected heading (e.g. a name sitting at
the very top with no heading at all) is simply not bucketed here -- contact
extraction handles that directly on the full block list.
"""

from services.parser.blocks import RawBlock
from services.parser.aliases import SECTION_ALIASES, UNSUPPORTED_ALIASES
from services.parser.heuristics import fuzzy_match_alias
from shared.schemas.portfolio import ParseWarning


def classify_sections(
    blocks: list[RawBlock],
) -> tuple[dict[str, list[RawBlock]], dict[str, list[str]], list[ParseWarning]]:
    sections: dict[str, list[RawBlock]] = {}
    uncategorized: dict[str, list[str]] = {}
    warnings: list[ParseWarning] = []

    current_key: str | None = None
    current_is_supported: bool = True
    pending_boundary: bool = False

    for block in blocks:
        if block.is_heading:
            supported_key, supported_score = fuzzy_match_alias(
                block.text, SECTION_ALIASES
            )
            unsupported_key, unsupported_score = fuzzy_match_alias(
                block.text, UNSUPPORTED_ALIASES
            )

            if supported_key == "contact":
                current_key = None
                continue
            elif supported_key and supported_score >= unsupported_score:
                current_key = supported_key
                current_is_supported = True
                sections.setdefault(current_key, [])
            elif unsupported_key:
                current_key = unsupported_key
                current_is_supported = False
                uncategorized.setdefault(current_key, [])
            else:
                current_key = block.text
                current_is_supported = False
                uncategorized.setdefault(current_key, [])
                warnings.append(
                    ParseWarning(
                        section="document",
                        message=(
                            f"Heading '{block.text}' didn't match any known "
                            f"section -- content moved to uncategorized."
                        ),
                        severity="warn",
                    )
                )
            pending_boundary = True
            continue

        if current_key is None:
            continue

        if pending_boundary:
            block.section_boundary = True
            pending_boundary = False

        if current_is_supported:
            sections[current_key].append(block)
        else:
            uncategorized[current_key].append(block.text)

    return sections, uncategorized, warnings