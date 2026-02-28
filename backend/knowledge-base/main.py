"""
Knowledge Base Retriever Service — Port 8003
============================================
Exposes a /retrieve endpoint used by the Tutor Service.
Queries Pinecone with the student's question + class/subject filters.
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# ── Globals ──────────────────────────────────────────────────────────────────
_model: Optional[SentenceTransformer] = None
_index = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _model, _index
    logger.info("Loading embedding model ...")
    _model = SentenceTransformer(os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"))

    api_key = os.getenv("PINECONE_API_KEY", "")
    if not api_key:
        raise RuntimeError("PINECONE_API_KEY not set")
    pc = Pinecone(api_key=api_key)
    _index = pc.Index(os.getenv("PINECONE_INDEX_NAME", "cbse-tutor"))
    logger.info("Knowledge Base service ready.")
    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="CBSE Knowledge Base Service",
    description="Retrieves relevant CBSE syllabus/NCERT chunks from Pinecone",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Schemas ──────────────────────────────────────────────────────────────────
class RetrieveRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=1000)
    class_no: Optional[int] = Field(None, ge=6, le=12)
    subject: Optional[str] = Field(None, description="science | social_science")
    top_k: int = Field(5, ge=1, le=10)


class RetrievedChunk(BaseModel):
    id: str
    text: str
    score: float
    source: str
    subject: Optional[str]
    class_no: Optional[int]
    chapter_title: Optional[str]


class RetrieveResponse(BaseModel):
    query: str
    chunks: list[RetrievedChunk]
    total_found: int


# ── Helpers ──────────────────────────────────────────────────────────────────
def build_filter(class_no: Optional[int], subject: Optional[str]) -> Optional[dict]:
    """Build Pinecone metadata filter."""
    filters = {}
    if class_no is not None:
        filters["class"] = {"$eq": class_no}
    if subject:
        filters["subject"] = {"$eq": subject}
    return filters if filters else None


# ── Routes ───────────────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {"status": "ok", "service": "knowledge-base"}


@app.post("/retrieve", response_model=RetrieveResponse)
async def retrieve(req: RetrieveRequest):
    if _model is None or _index is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    # Embed the query
    embedding = _model.encode(req.query, normalize_embeddings=True).tolist()

    # Build optional metadata filter
    metadata_filter = build_filter(req.class_no, req.subject)

    # Query Pinecone
    try:
        results = _index.query(
            vector=embedding,
            top_k=req.top_k,
            include_metadata=True,
            filter=metadata_filter,
        )
    except Exception as e:
        logger.error(f"Pinecone query failed: {e}")
        raise HTTPException(status_code=502, detail="Vector DB query failed")

    chunks = []
    for match in results.get("matches", []):
        meta = match.get("metadata", {})
        chunks.append(
            RetrievedChunk(
                id=match["id"],
                text=meta.get("text", ""),
                score=round(match["score"], 4),
                source=meta.get("source", "unknown"),
                subject=meta.get("subject"),
                class_no=meta.get("class"),
                chapter_title=meta.get("chapter_title"),
            )
        )

    return RetrieveResponse(
        query=req.query,
        chunks=chunks,
        total_found=len(chunks),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8003, reload=True)
