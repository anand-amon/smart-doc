import os, json, logging
from typing import List
from openai import OpenAI

logger = logging.getLogger("smartdoc")


class LLMProcessor:
    """
    Handles:
    - Document field extraction (Kimi K2 or OpenAI)
    - Query answering (router uses this client)
    - ALWAYS uses OpenAI for embeddings
    """

    def __init__(self):
        # -----------------------------
        # Load environment flags & keys
        # -----------------------------
        self.use_kimi = os.getenv("USE_KIMI_API", "false").lower() == "true"

        self.kimi_key = os.getenv("KIMI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

        logger.info(f"[LLM] Using Kimi? {self.use_kimi}")
        logger.info(f"[LLM] KIMI key present? {bool(self.kimi_key)}")
        logger.info(f"[LLM] OPENAI key present? {bool(self.openai_key)}")

        # -----------------------------
        # 1. Reasoning Client (Kimi OR OpenAI)
        # -----------------------------
        if self.use_kimi:
            if not self.kimi_key:
                logger.error("KIMI_API_KEY missing!")
            self.client = OpenAI(
                api_key=self.kimi_key,
                base_url="https://api.moonshot.ai/v1"
            )
            self.model = "kimi-k2-0905-preview"
            logger.info("[LLM] Kimi reasoning model initialized.")

        else:
            if not self.openai_key:
                logger.error("OPENAI_API_KEY missing!")
            self.client = OpenAI(api_key=self.openai_key)
            self.model = "gpt-4o"
            logger.info("[LLM] OpenAI reasoning model initialized.")

        # -----------------------------
        # 2. Embedding Client (ALWAYS OpenAI)
        # -----------------------------
        if not self.openai_key:
            logger.error("OPENAI_API_KEY required for embeddings!")
        
        self.embed_client = OpenAI(api_key=self.openai_key)
        self.embed_model = "text-embedding-3-small"
        logger.info("[LLM] OpenAI embedding model initialized.")

    # -------------------------------------------------------------------------
    # EXTRACT STRUCTURED FIELDS FROM OCR TEXT
    # -------------------------------------------------------------------------
    def extract_fields(self, document_text: str):
        """
        Use reasoning model (Kimi or OpenAI) to extract key invoice fields.
        """
        prompt = f"""
        Extract these exact fields and return ONLY valid JSON:

        - invoice_number
        - date
        - total_amount
        - vendor

        Document text:
        {document_text[:4000]}
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert document extraction assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )

            content = response.choices[0].message.content
            logger.warning(f"RAW LLM OUTPUT >>> {content}")

            # Remove code fences
            if "```" in content:
                parts = content.split("```")
                # pick inside JSON code block
                for p in parts:
                    if "{" in p and "}" in p:
                        content = p.strip()
                        break

            expected = ["invoice_number", "date", "total_amount", "vendor"]

            try:
                parsed = json.loads(content)
                clean = {k: parsed.get(k) for k in expected}
                return clean

            except Exception as e:
                logger.error(f"JSON parsing failed: {e}")
                return {k: None for k in expected}

        except Exception as e:
            logger.error(f"LLM extraction failed: {e}", exc_info=True)
            return {"error": str(e)}

    # -------------------------------------------------------------------------
    # EMBEDDINGS (ALWAYS OPENAI)
    # -------------------------------------------------------------------------
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Convert texts into vectors using OpenAI's embedding API.
        """
        try:
            resp = self.embed_client.embeddings.create(
                model=self.embed_model,
                input=texts
            )
            return [item.embedding for item in resp.data]

        except Exception as e:
            logger.error(f"Embedding failed: {e}", exc_info=True)
            raise
