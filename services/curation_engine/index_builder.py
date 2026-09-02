"""
Builds per-category, in-memory FAISS indices from a parsed Portfolio.
No persistence — rebuilt fresh on every upload (locked decision).
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import faiss
import numpy as np
from pydantic import BaseModel

from shared.schemas.portfolio import PortfolioData
from services.curation_engine.embedder import (
    EMBEDDING_DIM,
    MODEL_NAME,
    embed_texts,
    project_to_text,
    experience_to_text,
    certification_to_text,
    uncategorized_to_text,
)

CATEGORIES = ("projects", "experience", "certifications", "other")


class IndexMeta(BaseModel):
    model_name: str
    dimension: int
    timestamp: datetime
    entry_count: dict[str, int]


@dataclass
class CurationIndex:
    """In-memory bundle: one FAISS index + one ordered entry list per category.
    entry_map[category][i] is the source object for indices[category] row i —
    FAISS returns row positions, this is how we map back to real entries."""
    indices: dict[str, faiss.Index] = field(default_factory=dict)
    entry_map: dict[str, list[Any]] = field(default_factory=dict)
    meta: IndexMeta = None


def _build_category_index(texts: list[str]) -> faiss.Index:
    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    if texts:
        vectors = embed_texts(texts)
        index.add(vectors)
    return index


def build_indices(portfolio: PortfolioData) -> CurationIndex:
    result = CurationIndex()

     # projects
    proj_texts = [project_to_text(p) for p in portfolio.projects]
    result.indices["projects"] = _build_category_index(proj_texts)
    result.entry_map["projects"] = list(portfolio.projects)


    # experience
    exp_texts = [experience_to_text(e) for e in portfolio.experience]
    result.indices["experience"] = _build_category_index(exp_texts)
    result.entry_map["experience"] = list(portfolio.experience)


    # certifications
    cert_texts = [certification_to_text(c) for c in portfolio.certifications]
    result.indices["certifications"] = _build_category_index(cert_texts)
    result.entry_map["certifications"] = list(portfolio.certifications)

    # other (uncategorized) — dict[str, list[str]]: each value is a list of
    # plain strings under a section name, not a list of dicts
    other_items = []
    other_texts = []
    for section_name, items in (portfolio.uncategorized or {}).items():
        for raw_str in items:
            other_items.append({"section": section_name, "raw": raw_str})
            other_texts.append(uncategorized_to_text(raw_str))
    result.indices["other"] = _build_category_index(other_texts)
    result.entry_map["other"] = other_items

    result.meta = IndexMeta(
        model_name=MODEL_NAME,
        dimension=EMBEDDING_DIM,
        timestamp=datetime.now(timezone.utc),
        entry_count={cat: len(result.entry_map[cat]) for cat in CATEGORIES},
    )
    return result