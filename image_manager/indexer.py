from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import imagehash
import numpy as np
from PIL import Image

from .models import get_captioner, get_embedding_model, get_ocr_reader

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


@dataclass
class IndexedImage:
    path: str
    file_hash: str
    phash: str
    size: int
    mtime: float
    width: int
    height: int
    caption: str
    ocr_text: str
    tags: str
    embedding: bytes | None


def to_embedding_blob(vec: np.ndarray) -> bytes:
    arr = np.asarray(vec, dtype=np.float32)
    return arr.tobytes()


def compute_file_hash(file_path: Path) -> str:
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()


def image_to_rgb(file_path: Path) -> Image.Image:
    with Image.open(file_path) as im:
        return im.convert("RGB")


def parse_ocr_text(ocr_output: list) -> str:
    pieces = []
    for item in ocr_output:
        if len(item) >= 2:
            pieces.append(str(item[1]))
    return " ".join(pieces)


def build_record(
    file_path: Path,
    *,
    enable_semantic: bool = True,
    enable_caption: bool = True,
    enable_ocr: bool = True,
) -> IndexedImage:
    img = image_to_rgb(file_path)
    embedding = None
    caption = ""
    ocr_text = ""

    if enable_semantic:
        emb_model = get_embedding_model()
        vec = emb_model.encode([img], convert_to_numpy=True, normalize_embeddings=True)[0]
        embedding = to_embedding_blob(vec)

    if enable_caption:
        captioner = get_captioner()
        caption = captioner(img, max_new_tokens=24)[0].get("generated_text", "")

    if enable_ocr:
        ocr_reader = get_ocr_reader()
        ocr_out = ocr_reader.readtext(np.array(img))
        ocr_text = parse_ocr_text(ocr_out)

    tags = " ".join(token for token in [caption, ocr_text] if token)
    stat = file_path.stat()
    phash = str(imagehash.phash(img))
    return IndexedImage(
        path=str(file_path),
        file_hash=compute_file_hash(file_path),
        phash=phash,
        size=stat.st_size,
        mtime=stat.st_mtime,
        width=img.width,
        height=img.height,
        caption=caption,
        ocr_text=ocr_text,
        tags=tags,
        embedding=embedding,
    )


def upsert_record(conn, rec: IndexedImage) -> None:
    conn.execute(
        """
        INSERT INTO images (
            path, file_hash, phash, size, mtime, width, height,
            caption, ocr_text, tags, embedding, indexed_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            file_hash=excluded.file_hash,
            phash=excluded.phash,
            size=excluded.size,
            mtime=excluded.mtime,
            width=excluded.width,
            height=excluded.height,
            caption=excluded.caption,
            ocr_text=excluded.ocr_text,
            tags=excluded.tags,
            embedding=excluded.embedding,
            indexed_at=excluded.indexed_at
        """,
        (
            rec.path,
            rec.file_hash,
            rec.phash,
            rec.size,
            rec.mtime,
            rec.width,
            rec.height,
            rec.caption,
            rec.ocr_text,
            rec.tags,
            rec.embedding,
            datetime.utcnow().isoformat(),
        ),
    )


def scan_and_index(
    conn,
    image_dir: str | Path,
    progress_cb=None,
    *,
    enable_semantic: bool = True,
    enable_caption: bool = True,
    enable_ocr: bool = True,
) -> dict:
    root = Path(image_dir)
    files = [p for p in root.rglob("*") if p.suffix.lower() in IMAGE_EXTS]

    indexed = 0
    skipped = 0
    failed = []

    for idx, file_path in enumerate(files, start=1):
        try:
            stat = file_path.stat()
            current = conn.execute(
                "SELECT mtime, size FROM images WHERE path = ?", (str(file_path),)
            ).fetchone()
            if current and float(current["mtime"]) == stat.st_mtime and int(current["size"]) == stat.st_size:
                skipped += 1
            else:
                rec = build_record(
                    file_path,
                    enable_semantic=enable_semantic,
                    enable_caption=enable_caption,
                    enable_ocr=enable_ocr,
                )
                upsert_record(conn, rec)
                indexed += 1

            if progress_cb:
                progress_cb(idx, len(files), file_path.name)
        except Exception as ex:  # noqa: BLE001
            failed.append((str(file_path), str(ex)))

    conn.commit()
    return {
        "total": len(files),
        "indexed": indexed,
        "skipped": skipped,
        "failed": failed,
    }


def embedding_from_blob(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)
