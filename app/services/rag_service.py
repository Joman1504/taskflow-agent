# app/services/rag_service.py
# RAG service: chunks transcripts, embeds them via OpenAI, and persists
# embeddings in ChromaDB. On retrieval, returns the most relevant chunks
# to be injected as background context into the LLM prompts.

import hashlib
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings as app_settings
from app.services.llm_client import get_client

# ── Constants ─────────────────────────────────────────────────────────────────

_COLLECTION_NAME = "taskflow_transcripts"
_EMBED_MODEL     = "text-embedding-3-small"
_CHUNK_SIZE      = 800   # characters per chunk
_CHUNK_OVERLAP   = 150   # character overlap between consecutive chunks
_QUERY_MAX_CHARS = 2000  # truncate query before embedding to keep costs low

# ── Singletons ────────────────────────────────────────────────────────────────

_chroma_client: chromadb.ClientAPI | None = None
_collection: chromadb.Collection | None = None


def _get_collection() -> chromadb.Collection:
    """Return (or lazily create) the persistent ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is None:
        _chroma_client = chromadb.PersistentClient(
            path=app_settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        _collection = _chroma_client.get_or_create_collection(
            name=_COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


# ── Text chunking ─────────────────────────────────────────────────────────────

def _chunk_text(text: str) -> list[str]:
    """
    Split *text* into overlapping fixed-size character chunks.
    Returns only non-empty chunks.
    """
    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunk = text[start : start + _CHUNK_SIZE]
        if chunk.strip():
            chunks.append(chunk)
        start += _CHUNK_SIZE - _CHUNK_OVERLAP
    return chunks


# ── Embedding ─────────────────────────────────────────────────────────────────

async def _embed(texts: list[str]) -> list[list[float]]:
    """Embed a list of strings using OpenAI and return the embedding vectors."""
    client = get_client()
    response = await client.embeddings.create(model=_EMBED_MODEL, input=texts)
    return [item.embedding for item in response.data]


# ── Public API ────────────────────────────────────────────────────────────────

async def index_transcript(transcript: str) -> None:
    """
    Chunk, embed, and persist *transcript* in the vector store.
    Silently skips the document if it has already been indexed
    (identified by a SHA-256 hash of the raw text).
    """
    doc_id = hashlib.sha256(transcript.encode()).hexdigest()[:20]
    collection = _get_collection()

    # Idempotency check — avoid re-embedding the same transcript
    existing = collection.get(where={"doc_id": {"$eq": doc_id}}, limit=1)
    if existing["ids"]:
        return

    chunks = _chunk_text(transcript)
    if not chunks:
        return

    embeddings = await _embed(chunks)
    ids        = [f"{doc_id}:{i}" for i in range(len(chunks))]
    metadatas  = [{"doc_id": doc_id, "chunk_idx": i} for i in range(len(chunks))]

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=chunks,
        metadatas=metadatas,
    )


async def retrieve_context(query: str, n_results: int = 5) -> str:
    """
    Embed the query and return the top-*n_results* most semantically
    similar chunks from the knowledge base, joined by separators.
    Returns an empty string when the store is empty.
    """
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        return ""

    query_embedding = await _embed([query[:_QUERY_MAX_CHARS]])
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=min(n_results, count),
        include=["documents"],
    )

    chunks: list[str] = results["documents"][0] if results["documents"] else []
    return "\n\n---\n\n".join(chunks)


def get_stats() -> dict:
    """Return basic statistics about the vector knowledge base."""
    collection = _get_collection()
    return {
        "indexed_chunks": collection.count(),
        "collection": _COLLECTION_NAME,
    }
