# backend/pipeline/embeddings.py
from typing import List
from config import settings

# You already have Kimi K2 client somewhere;
# plug the same auth style you use in DocumentProcessor.
# This is pseudocode wrapper.
import requests

def kimi_embed(texts: List[str]) -> List[List[float]]:
    """
    Batch embed using Kimi (replace endpoint/model with your actual).
    Returns list of embedding vectors.
    """
    url = settings.kimi_embed_url   # add in config
    headers = {"Authorization": f"Bearer {settings.kimi_api_key}"}

    payload = {
        "model": settings.kimi_embed_model,
        "input": texts
    }

    r = requests.post(url, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    data = r.json()

    # adapt to Kimi response shape
    return [item["embedding"] for item in data["data"]]
