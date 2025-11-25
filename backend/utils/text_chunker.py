# backend/utils/text_chunker.py
from typing import List

def chunk_text(text: str, max_chars: int = 1500, overlap: int = 200) -> List[str]:
    """
    Simple char-based chunking to avoid tokenizers.
    max_chars ~ 300-500 tokens depending on language.
    """
    if not text:
        return []

    chunks = []
    start = 0
    n = len(text)

    while start < n:
        end = min(start + max_chars, n)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end - overlap  # overlap for context continuity
        if start < 0:
            start = 0

    return chunks
