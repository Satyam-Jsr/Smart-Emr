"""Simple CPU-friendly RAG prototype: chunk notes, compute embeddings with
sentence-transformers, build an hnswlib index, and provide a retrieval API.

Usage:
  python rag_prototype.py build   # builds the index from the DB
  python rag_prototype.py query --patient 1 --q "shortness of breath" --k 5

Notes: designed for local CPU use. Uses sentence-transformers 'all-MiniLM-L6-v2'.
Index stored as 'rag_index.bin' and metadata as 'rag_meta.json' in the backend folder.
"""
from __future__ import annotations

import json
import os
import argparse
from typing import List, Dict, Tuple

import numpy as np

from sentence_transformers import SentenceTransformer

# hnswlib is easier to install on Windows than faiss; fall back to simple search if unavailable
try:
    import hnswlib
    HAS_HNSW = True
except Exception:
    HAS_HNSW = False

from app.database import SessionLocal
from app.models import Note

HERE = os.path.dirname(__file__)
INDEX_PATH = os.path.join(HERE, "rag_index.bin")
META_PATH = os.path.join(HERE, "rag_meta.json")
EMB_MODEL_NAME = "all-MiniLM-L6-v2"


def fetch_notes(db, patient_id: int | None = None) -> List[Dict]:
    q = db.query(Note)
    if patient_id is not None:
        q = q.filter(Note.patient_id == patient_id)
    notes = q.order_by(Note.note_date.desc()).all()
    return [{"id": n.id, "patient_id": n.patient_id, "text": n.text or "", "note_date": n.note_date.isoformat()} for n in notes]


def chunk_text(text: str, max_tokens: int = 200, overlap: int = 50) -> List[str]:
    # Simple whitespace-based chunker tuned for sentences; keep it conservative for embeddings
    words = text.split()
    if len(words) <= max_tokens:
        return [text]
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i+max_tokens]
        chunks.append(" ".join(chunk))
        i += max_tokens - overlap
    return chunks


class RAGIndex:
    def __init__(self, model_name: str = EMB_MODEL_NAME):
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.meta: List[Dict] = []

    def build(self, rebuild: bool = False):
        db = SessionLocal()
        all_notes = fetch_notes(db)
        db.close()

        # flatten into chunks
        texts = []
        meta = []
        for n in all_notes:
            chunks = chunk_text(n["text"]) if n["text"] else []
            if not chunks:
                continue
            for c in chunks:
                meta.append({"note_id": n["id"], "patient_id": n["patient_id"], "text_snippet": c, "note_date": n["note_date"]})
                texts.append(c)

        if not texts:
            # nothing to index
            self.meta = []
            self.index = None
            self._save_meta()
            return

        embeddings = self.model.encode(texts, show_progress_bar=True, convert_to_numpy=True)

        dim = embeddings.shape[1]

        if HAS_HNSW:
            p = hnswlib.Index(space='cosine', dim=dim)
            p.init_index(max_elements=len(embeddings), ef_construction=200, M=16)
            p.add_items(embeddings, np.arange(len(embeddings)))
            p.set_ef(50)
            self.index = p
            # persist
            p.save_index(INDEX_PATH)
        else:
            # fallback: save embeddings to disk and use brute-force search
            np.save(os.path.join(HERE, "rag_embeddings.npy"), embeddings)
            self.index = None

        self.meta = meta
        self._save_meta()

    def _save_meta(self):
        with open(META_PATH, "w", encoding="utf-8") as f:
            json.dump(self.meta, f, ensure_ascii=False, indent=2)

    def load(self):
        # load meta
        if not os.path.exists(META_PATH):
            self.meta = []
        else:
            with open(META_PATH, "r", encoding="utf-8") as f:
                self.meta = json.load(f)

        if HAS_HNSW and os.path.exists(INDEX_PATH):
            # load hnsw index
            # infer dim from saved embeddings if available; otherwise use model to get dim
            try:
                # create empty index and load
                dim = self.model.get_sentence_embedding_dimension()
                p = hnswlib.Index(space='cosine', dim=dim)
                p.load_index(INDEX_PATH)
                p.set_ef(50)
                self.index = p
            except Exception:
                self.index = None
        else:
            self.index = None

    def query(self, patient_id: int | None, q: str, k: int = 5) -> List[Tuple[float, Dict]]:
        """Return list of (score, meta) for top-k relevant chunks for the patient_id (or all patients if None)."""
        if not self.meta:
            self.load()
        if not self.meta:
            return []

        query_emb = self.model.encode([q], convert_to_numpy=True)

        # candidate filtering by patient_id
        candidate_indices = [i for i, m in enumerate(self.meta) if (patient_id is None or m.get("patient_id") == patient_id)]
        if not candidate_indices:
            return []

        if self.index is not None:
            # query full index and then filter
            labels, distances = self.index.knn_query(query_emb, k=min(k*3, len(self.meta)))
            labels = labels[0].tolist()
            distances = distances[0].tolist()
            results = []
            for lbl, dist in zip(labels, distances):
                if lbl in candidate_indices:
                    results.append((1.0 - dist, self.meta[lbl]))
                    if len(results) >= k:
                        break
            return results
        else:
            # brute force using saved embeddings
            emb_path = os.path.join(HERE, "rag_embeddings.npy")
            if not os.path.exists(emb_path):
                return []
            embeddings = np.load(emb_path)
            cand_embs = embeddings[candidate_indices]
            # cosine similarity
            qn = query_emb / np.linalg.norm(query_emb, axis=1, keepdims=True)
            en = cand_embs / np.linalg.norm(cand_embs, axis=1, keepdims=True)
            sims = (en @ qn[0]).tolist()
            scored = sorted([(s, self.meta[candidate_indices[i]]) for i, s in enumerate(sims)], key=lambda x: x[0], reverse=True)
            return scored[:k]


def build_index_cli():
    r = RAGIndex()
    r.build()
    print("Index built. meta items:", len(r.meta))


def query_cli(patient: int | None, q: str, k: int = 5):
    r = RAGIndex()
    r.load()
    res = r.query(patient, q, k)
    for score, m in res:
        print(f"score={score:.4f} patient={m.get('patient_id')} note_id={m.get('note_id')} snippet={m.get('text_snippet')[:200]!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd")
    b = sub.add_parser("build")
    q = sub.add_parser("query")
    q.add_argument("--patient", type=int, default=None)
    q.add_argument("--q", type=str, required=True)
    q.add_argument("--k", type=int, default=5)

    args = parser.parse_args()
    if args.cmd == "build":
        build_index_cli()
    elif args.cmd == "query":
        query_cli(args.patient, args.q, args.k)
    else:
        parser.print_help()
