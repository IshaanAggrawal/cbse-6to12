"""
NCERT PDF Ingestion Pipeline for CBSE Student Tutor
====================================================
Drop NCERT PDFs into knowledge-base/data/ncert_pdfs/{subject}/class_{N}/
e.g.  knowledge-base/data/ncert_pdfs/science/class_10/chapter1.pdf

Run:  python knowledge-base/ingester.py
This will:
  1. Extract text from all PDFs
  2. Chunk text with overlap
  3. Create embeddings (sentence-transformers, local, free)
  4. Upsert to Pinecone with rich metadata
"""

import os
import json
import hashlib
import logging
from pathlib import Path
from typing import Generator

import fitz  # PyMuPDF
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone, ServerlessSpec
from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Config ──────────────────────────────────────────────────────────────────
PINECONE_API_KEY  = os.getenv("PINECONE_API_KEY", "")
INDEX_NAME        = os.getenv("PINECONE_INDEX_NAME", "cbse-tutor")
EMBEDDING_MODEL   = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
NCERT_PDF_DIR     = Path(os.getenv("NCERT_PDF_DIR", "./knowledge-base/data/ncert_pdfs"))
SYLLABUS_DIR      = Path("./knowledge-base/data")
CHUNK_SIZE        = int(os.getenv("CHUNK_SIZE", 500))
CHUNK_OVERLAP     = int(os.getenv("CHUNK_OVERLAP", 50))
BATCH_SIZE        = 100          # Pinecone upsert batch size
EMBEDDING_DIM     = 384          # all-MiniLM-L6-v2 output dimension


# ── Pinecone setup ─────────────────────────────────────────────────────────
def get_pinecone_index():
    if not PINECONE_API_KEY:
        raise ValueError("PINECONE_API_KEY not set in .env")
    pc = Pinecone(api_key=PINECONE_API_KEY)

    existing = [i.name for i in pc.list_indexes()]
    if INDEX_NAME not in existing:
        logger.info(f"Creating Pinecone index '{INDEX_NAME}' ...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=EMBEDDING_DIM,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        logger.info("Index created.")
    else:
        logger.info(f"Using existing Pinecone index '{INDEX_NAME}'.")

    return pc.Index(INDEX_NAME)


# ── Text extraction from PDF ────────────────────────────────────────────────
def extract_text_from_pdf(pdf_path: Path) -> str:
    """Extract full text from a PDF using PyMuPDF."""
    try:
        doc = fitz.open(str(pdf_path))
        text = ""
        for page in doc:
            text += page.get_text("text") + "\n"
        doc.close()
        return text.strip()
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return ""


# ── Chunking ────────────────────────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping word-based chunks."""
    words = text.split()
    chunks = []
    step = chunk_size - overlap
    for i in range(0, len(words), step):
        chunk = " ".join(words[i : i + chunk_size])
        if len(chunk.strip()) > 50:   # skip tiny chunks
            chunks.append(chunk.strip())
    return chunks


# ── Metadata extraction from path ──────────────────────────────────────────
def parse_pdf_path(pdf_path: Path) -> dict:
    """
    Expects:  ncert_pdfs/{subject}/class_{N}/{chapter_or_file}.pdf
    Returns metadata dict.
    """
    parts = pdf_path.parts
    try:
        subject_idx = next(i for i, p in enumerate(parts) if p == "ncert_pdfs") + 1
        subject = parts[subject_idx].lower()
        class_folder = parts[subject_idx + 1]          # e.g. "class_10"
        class_no = int(class_folder.split("_")[1])
    except (StopIteration, IndexError, ValueError):
        subject = "unknown"
        class_no = 0

    return {
        "subject": subject,
        "class": class_no,
        "filename": pdf_path.name,
        "source": "ncert_pdf",
    }


# ── Syllabus JSON ingestion (chapter/topic metadata) ───────────────────────
def load_syllabus_text_chunks() -> list[dict]:
    """
    Convert syllabus JSONs into chunks + metadata.
    These are lightweight textual descriptions of syllabus structure.
    """
    chunks = []
    for json_path in SYLLABUS_DIR.rglob("*.json"):
        try:
            with open(json_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            logger.warning(f"Skipping {json_path}: {e}")
            continue

        subject = data.get("subject", "unknown")
        class_no = data.get("class", 0)
        board = data.get("board", "CBSE")
        books_list = data.get("books", [])

        for chapter in data.get("chapters", []):
            book_name = chapter.get("book", books_list[0] if books_list else subject)
            chapter_no = chapter.get("chapter_no", 0)
            title = chapter.get("title", "")
            topics = chapter.get("topics", [])

            # Build a descriptive text block for this chapter
            topics_str = "; ".join(topics)
            text = (
                f"[CBSE {board} Class {class_no} | {subject.replace('_', ' ').title()} | "
                f"Book: {book_name} | Chapter {chapter_no}: {title}]\n"
                f"Topics covered: {topics_str}"
            )

            uid = hashlib.md5(text.encode()).hexdigest()
            chunks.append({
                "id": f"syllabus_{uid}",
                "text": text,
                "metadata": {
                    "source": "syllabus_json",
                    "subject": subject,
                    "class": class_no,
                    "book": book_name,
                    "chapter_no": chapter_no,
                    "chapter_title": title,
                    "board": board,
                },
            })

    logger.info(f"Loaded {len(chunks)} syllabus chunks from JSON files.")
    return chunks


# ── PDF ingestion ────────────────────────────────────────────────────────────
def load_pdf_text_chunks() -> list[dict]:
    """Walk ncert_pdfs directory and return chunks from all PDFs."""
    chunks = []
    pdf_paths = list(NCERT_PDF_DIR.rglob("*.pdf"))

    if not pdf_paths:
        logger.warning(
            f"No PDFs found in '{NCERT_PDF_DIR}'. "
            "Place NCERT PDFs in knowledge-base/data/ncert_pdfs/{{subject}}/class_{{N}}/"
        )
        return []

    for pdf_path in pdf_paths:
        logger.info(f"Processing PDF: {pdf_path}")
        meta = parse_pdf_path(pdf_path)
        raw_text = extract_text_from_pdf(pdf_path)
        if not raw_text:
            continue

        text_chunks = chunk_text(raw_text)
        for idx, chunk in enumerate(text_chunks):
            uid = hashlib.md5(f"{pdf_path}{idx}".encode()).hexdigest()
            chunks.append({
                "id": f"pdf_{uid}",
                "text": chunk,
                "metadata": {**meta, "chunk_index": idx},
            })

    logger.info(f"Extracted {len(chunks)} chunks from {len(pdf_paths)} PDFs.")
    return chunks


# ── Batch upsert to Pinecone ────────────────────────────────────────────────
def batch_upsert(index, records: list[dict], model: SentenceTransformer):
    """Embed and upsert records in batches."""
    texts = [r["text"] for r in records]

    logger.info(f"Embedding {len(texts)} chunks ...")
    embeddings = model.encode(texts, batch_size=32, show_progress_bar=True, normalize_embeddings=True)

    vectors = []
    for record, embedding in zip(records, embeddings):
        vectors.append({
            "id": record["id"],
            "values": embedding.tolist(),
            "metadata": {**record["metadata"], "text": record["text"][:1000]},  # store first 1000 chars
        })

    # Upsert in batches
    for i in tqdm(range(0, len(vectors), BATCH_SIZE), desc="Upserting to Pinecone"):
        batch = vectors[i : i + BATCH_SIZE]
        index.upsert(vectors=batch)

    logger.info(f"Upserted {len(vectors)} vectors to Pinecone index '{INDEX_NAME}'.")


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    logger.info("=== CBSE Tutor — Knowledge Base Ingestion ===")

    # Load embedding model (runs locally, no API needed)
    logger.info(f"Loading embedding model: {EMBEDDING_MODEL} ...")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Connect to Pinecone
    index = get_pinecone_index()

    # Gather all chunks
    all_chunks = []
    all_chunks.extend(load_syllabus_text_chunks())
    all_chunks.extend(load_pdf_text_chunks())

    if not all_chunks:
        logger.warning("No content to index. Exiting.")
        return

    # Remove duplicates by ID
    seen = set()
    unique_chunks = []
    for c in all_chunks:
        if c["id"] not in seen:
            seen.add(c["id"])
            unique_chunks.append(c)

    logger.info(f"Total unique chunks to index: {len(unique_chunks)}")

    # Embed and upsert
    batch_upsert(index, unique_chunks, model)
    logger.info("✅ Ingestion complete! Knowledge base is ready.")

    # Print index stats
    stats = index.describe_index_stats()
    logger.info(f"Index stats: {stats}")


if __name__ == "__main__":
    main()
