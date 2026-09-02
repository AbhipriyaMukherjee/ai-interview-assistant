"""
Embeds a target-role text and queries each category index independently,
returning top-K per category (not one global top-K — locked decision).
"""

from dataclasses import dataclass
from typing import Any

from services.curation_engine.embedder import embed_texts
from services.curation_engine.index_builder import CurationIndex, CATEGORIES

DEFAULT_TOP_K = 5


@dataclass
class RankedEntry:
    entry: Any
    score: float          # cosine similarity, [-1, 1], typically [0, 1] in practice
    category: str


@dataclass
class RoleMatchResult:
    role_text: str
    by_category: dict[str, list[RankedEntry]]


def match_role(
    role_text: str,
    index: CurationIndex,
    top_k: int = DEFAULT_TOP_K,
) -> RoleMatchResult:
    role_vector = embed_texts([role_text])  # shape (1, EMBEDDING_DIM)

    by_category: dict[str, list[RankedEntry]] = {}
    for category in CATEGORIES:
        faiss_index = index.indices[category]
        entries = index.entry_map[category]

        if faiss_index.ntotal == 0:
            by_category[category] = []
            continue

        k = min(top_k, faiss_index.ntotal)
        scores, positions = faiss_index.search(role_vector, k)

        ranked = [
            RankedEntry(entry=entries[pos], score=float(score), category=category)
            for score, pos in zip(scores[0], positions[0])
            if pos != -1
        ]
        by_category[category] = ranked

    return RoleMatchResult(role_text=role_text, by_category=by_category)