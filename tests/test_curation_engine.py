from services.curation_engine.index_builder import CATEGORIES, build_indices
from services.parser.router import parse_portfolio
from services.curation_engine.embedder import EMBEDDING_DIM, MODEL_NAME
from services.curation_engine.role_matcher import match_role

FIXTURE = "tests/fixtures/portfolios/Persona_2_Over_Achiever.docx"


def test_faiss_entry_map_counts_match():
    portfolio = parse_portfolio(FIXTURE)
    curation_index = build_indices(portfolio)

    for category in CATEGORIES:
        faiss_count = curation_index.indices[category].ntotal
        entry_count = len(curation_index.entry_map[category])

        assert faiss_count == entry_count, (
            f"{category}: FAISS has {faiss_count} vectors, "
            f"but entry_map has {entry_count} entries"
        )

def test_index_metadata_matches_index():
    portfolio = parse_portfolio(FIXTURE)
    curation_index = build_indices(portfolio)

    assert curation_index.meta.model_name == MODEL_NAME
    assert curation_index.meta.dimension == EMBEDDING_DIM

    for category in CATEGORIES:
        assert curation_index.meta.entry_count[category] == len(
            curation_index.entry_map[category]
        )

def test_role_match_returns_top_k_per_category():
    portfolio = parse_portfolio(FIXTURE)
    curation_index = build_indices(portfolio)

    top_k = 2
    result = match_role(
        "Backend Software Engineer",
        curation_index,
        top_k=top_k,
    )

    for category in CATEGORIES:
        matches = result.by_category[category]

        assert len(matches) <= top_k, (
            f"{category}: returned {len(matches)} results, "
            f"expected at most {top_k}"
        )

        assert len(matches) <= len(curation_index.entry_map[category])


def test_role_match_scores_are_descending():
    portfolio = parse_portfolio(FIXTURE)
    curation_index = build_indices(portfolio)

    result = match_role(
        "Backend Software Engineer",
        curation_index,
        top_k=5,
    )

    for category in CATEGORIES:
        matches = result.by_category[category]
        scores = [match.score for match in matches]

        assert scores == sorted(scores, reverse=True), (
            f"{category}: scores are not in descending order: {scores}"
        )

def test_role_match_handles_empty_categories():
    portfolio = parse_portfolio(
        "tests/fixtures/portfolios/Persona_8_Bare_Minimum.docx"
    )
    curation_index = build_indices(portfolio)

    result = match_role(
        "Backend Software Engineer",
        curation_index,
        top_k=5,
    )

    for category in CATEGORIES:
        assert category in result.by_category

        if curation_index.indices[category].ntotal == 0:
            assert result.by_category[category] == []