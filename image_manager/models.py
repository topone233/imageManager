from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def get_embedding_model():
    from sentence_transformers import SentenceTransformer

    return SentenceTransformer("clip-ViT-B-32")


@lru_cache(maxsize=1)
def get_captioner():
    from transformers import pipeline

    return pipeline("image-to-text", model="Salesforce/blip-image-captioning-base")


@lru_cache(maxsize=1)
def get_ocr_reader():
    import easyocr

    # 中文 + 英文，覆盖常见 IM 截图与表情文本
    return easyocr.Reader(["ch_sim", "en"], gpu=False)
