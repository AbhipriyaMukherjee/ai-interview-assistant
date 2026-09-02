"""
Day 3 validation pass: does certification similarity behave differently
from project/experience similarity, or does it just look that way because
of persona composition?

This script is read-only against the pipeline. It does not tune, threshold,
or weight anything — it only captures raw FAISS output across personas.

Run from repo root: python -m tests.validation.day3_cert_score_validation
"""

import csv
from pathlib import Path

from services.parser.router import parse_portfolio  # adjust import if router exposes it differently
from services.curation_engine.index_builder import build_indices, CATEGORIES
from services.curation_engine.role_matcher import match_role

FIXTURES_DIR = Path("tests/fixtures/portfolios")
OUTPUT_CSV = Path("tests/validation/day3_cert_score_results.csv")

ROLE_QUERIES = [
    "Backend Software Engineer",
    "Frontend Software Engineer",
    "Full Stack Software Engineer",
    "Data Scientist / Machine Learning Engineer",
    "DevOps / Cloud Engineer",
]

# Use .docx fixtures only for this pass — PDF vs DOCX parsing fidelity is a
# separate question from cert-scoring behavior, and mixing formats would
# muddy this specific experiment.
PERSONA_FILES = sorted(FIXTURES_DIR.glob("*.docx"))


def entry_label(category: str, entry) -> str:
    """Human-readable identifier for the manual relevance spot-check."""
    if category == "projects":
        return entry.name  # was: entry.title
    if category == "experience":
        label = entry.title or "Unknown role"
        if entry.company:
            label += f" @ {entry.company}"
        return label  # was: f"{entry.role} @ {entry.org}"
    if category == "certifications":
        return f"{entry.name} ({entry.issuer})" if entry.issuer else entry.name
    if category == "other":
        return f"[{entry['section']}] {str(entry['raw'])[:60]}"
    return "<unknown>"


def main():
    rows = []

    for persona_path in PERSONA_FILES:
        persona_name = persona_path.stem

        portfolio = parse_portfolio(str(persona_path))  # was: portfolio, warnings = ...
        index = build_indices(portfolio)

        entry_counts = index.meta.entry_count  # {category: count}

        for query in ROLE_QUERIES:
            # top_k = size of category so we capture every returned score,
            # not just a truncated top-K — variance across the full set
            # is part of the hypothesis, not just the top hit.
            max_k = max(entry_counts.values()) if entry_counts else 1
            result = match_role(query, index, top_k=max(max_k, 1))

            for category in CATEGORIES:
                ranked_entries = result.by_category[category]

                if not ranked_entries:
                    # Explicitly record the empty case rather than silently
                    # skipping it — zero-cert personas should show up as
                    # an empty result, not an absence of rows.
                    rows.append({
                        "persona": persona_name,
                        "query": query,
                        "category": category,
                        "rank": None,
                        "score": None,
                        "entry_label": None,
                        "n_projects": entry_counts.get("projects", 0),
                        "n_experience": entry_counts.get("experience", 0),
                        "n_certifications": entry_counts.get("certifications", 0),
                        "n_other": entry_counts.get("other", 0),
                    })
                    continue

                for rank, ranked in enumerate(ranked_entries, start=1):
                    rows.append({
                        "persona": persona_name,
                        "query": query,
                        "category": category,
                        "rank": rank,
                        "score": round(ranked.score, 4),
                        "entry_label": entry_label(category, ranked.entry),
                        "n_projects": entry_counts.get("projects", 0),
                        "n_experience": entry_counts.get("experience", 0),
                        "n_certifications": entry_counts.get("certifications", 0),
                        "n_other": entry_counts.get("other", 0),
                    })

    OUTPUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()