"""
Diagnostic: dumps raw blocks for a given section of a given docx, so we can
see the exact text/heading/bullet flags the parser is working with --
instead of guessing at document structure from memory.
"""
from services.parser import docx_extractor, section_classifier

def dump_section(file_path: str, section_key: str):
    blocks, warnings = docx_extractor.extract_blocks(file_path)
    sections, uncategorized, class_warnings = section_classifier.classify_sections(blocks)

    print(f"=== {file_path} :: section '{section_key}' ===")
    target = sections.get(section_key)
    if target is None:
        print(f"  (no such key in sections; available keys: {list(sections.keys())})")
        print(f"  uncategorized keys: {list(uncategorized.keys())}")
        return

    for b in target:
        print(f"  is_heading={b.is_heading!s:5} is_bullet={b.is_bullet!s:5} score={b.heading_score:3}  text={b.text!r}")

if __name__ == "__main__":
    dump_section("tests/fixtures/portfolios/Persona_5_Minimalist_Formatter.docx", "experience")
    print()
    dump_section("tests/fixtures/portfolios/Persona_5_Minimalist_Formatter.docx", "certifications")
    print()
    dump_section("tests/fixtures/portfolios/Persona_7_Overlapping_Timeline.docx", "projects")
    print()
    dump_section("tests/fixtures/portfolios/Persona_7_Overlapping_Timeline.docx", "experience")