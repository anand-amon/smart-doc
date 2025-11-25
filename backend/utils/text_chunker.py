# backend/utils/text_chunker.py
from typing import List

def chunk_text(text: str, size: int = 500, overlap: int = 50):
    if len(text) < size:
        return [text]  # never return empty list

    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        start += size - overlap
    return chunks
