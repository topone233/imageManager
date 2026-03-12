from __future__ import annotations

from datetime import datetime

import numpy as np

from .indexer import embedding_from_blob
from .models import get_embedding_model


def _keyword_score(query: str, caption: str, ocr_text: str, tags: str) -> float:
    q = query.lower().strip()
    if not q:
        return 0.0
    score = 0.0
    for field in [caption or "", ocr_text or "", tags or ""]:
        text = field.lower()
        if q in text:
            score += 0.25
        score += sum(0.03 for token in q.split() if token in text)
    return min(score, 0.8)


def keyword_search(conn, query: str, top_k: int = 20):
    rows = conn.execute(
        "SELECT id, path, caption, ocr_text, tags, use_count, last_used FROM images"
    ).fetchall()
    results = []
    for row in rows:
        kw_score = _keyword_score(query, row["caption"], row["ocr_text"], row["tags"])
        if kw_score > 0:
            results.append(
                {
                    "id": row["id"],
                    "path": row["path"],
                    "caption": row["caption"],
                    "ocr_text": row["ocr_text"],
                    "use_count": row["use_count"],
                    "last_used": row["last_used"],
                    "score": kw_score,
                }
            )
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def semantic_search(conn, query: str, top_k: int = 20):
    rows = conn.execute(
        "SELECT id, path, caption, ocr_text, tags, embedding, use_count, last_used FROM images"
    ).fetchall()
    if not rows:
        return []

    rows_with_emb = [row for row in rows if row["embedding"]]
    if not rows_with_emb:
        return keyword_search(conn, query, top_k)

    try:
        model = get_embedding_model()
        query_emb = model.encode([query], convert_to_numpy=True, normalize_embeddings=True)[0]
    except Exception:  # noqa: BLE001
        return keyword_search(conn, query, top_k)

    results = []
    for row in rows:
        kw_score = _keyword_score(query, row["caption"], row["ocr_text"], row["tags"])
        pop_score = min((row["use_count"] or 0) * 0.01, 0.2)
        sem_score = 0.0
        if row["embedding"]:
            emb = embedding_from_blob(row["embedding"])
            sem_score = float(np.dot(query_emb, emb))
        final = sem_score * 0.75 + kw_score + pop_score
        results.append(
            {
                "id": row["id"],
                "path": row["path"],
                "caption": row["caption"],
                "ocr_text": row["ocr_text"],
                "use_count": row["use_count"],
                "last_used": row["last_used"],
                "score": final,
            }
        )

    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def mark_used(conn, image_id: int, query: str = "") -> None:
    now = datetime.utcnow().isoformat()
    conn.execute(
        "UPDATE images SET use_count = COALESCE(use_count, 0) + 1, last_used = ? WHERE id = ?",
        (now, image_id),
    )
    conn.execute(
        "INSERT INTO usage_logs (image_id, event_type, query, ts) VALUES (?, 'used', ?, ?)",
        (image_id, query, now),
    )
    conn.commit()
