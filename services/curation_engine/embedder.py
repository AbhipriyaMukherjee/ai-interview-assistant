"""
Singleton Sentence-BERT embedder + entry-to-text conversion.
Model: all-MiniLM-L6-v2 (locked decision — do not swap without updating
IndexMeta.model_name and re-validating dimension downstream).
"""

from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer

from shared.schemas.portfolio import ProjectEntry, ExperienceEntry, CertificationEntry

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 output dim — validated against model.get_sentence_embedding_dimension() at load


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """Singleton loader. lru_cache ensures the model loads once per process,
    not once per request — Streamlit reruns the script on every interaction,
    so this matters more here than it would in a normal long-lived server."""
    model = SentenceTransformer(MODEL_NAME)
    assert model.get_embedding_dimension() == EMBEDDING_DIM, (
        f"Expected dim {EMBEDDING_DIM}, got "
        f"{model.get_embedding_dimension()}. Model artifact may have changed."
    )
    return model

def project_to_text(entry: ProjectEntry) -> str:
    parts = [entry.name]
    if entry.description:
        parts.append(entry.description)
    if entry.tech_stack:
        parts.append("Technologies: " + ", ".join(entry.tech_stack))
    if entry.bullets:
        parts.extend(b.text for b in entry.bullets)
    return ". ".join(p for p in parts if p)


def experience_to_text(entry: ExperienceEntry) -> str:
    parts = []
    if entry.title:
        role_line = entry.title
        if entry.company:
            role_line += f" at {entry.company}"
        parts.append(role_line)
    elif entry.company:
        parts.append(entry.company)
    if entry.bullets:
        parts.extend(b.text for b in entry.bullets)
    return ". ".join(p for p in parts if p)


def certification_to_text(entry: CertificationEntry) -> str:
    # unchanged — CertificationEntry matched the original assumption
    if entry.issuer:
        return f"{entry.name}, issued by {entry.issuer}"
    return entry.name


def uncategorized_to_text(item: str) -> str:
    """uncategorized values are plain strings (dict[str, list[str]]),
    not nested dicts — no flattening needed, just pass through."""
    return item

def embed_texts(texts: list[str]) -> np.ndarray:
    """Returns L2-normalized embeddings so FAISS IndexFlatIP gives cosine similarity."""
    if not texts:
        return np.empty((0, EMBEDDING_DIM), dtype="float32")
    model = get_embedder()
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(vectors, dtype="float32")