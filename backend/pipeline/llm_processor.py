import os, json, logging
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMProcessor:
    def __init__(self):
        self.use_kimi = os.getenv("USE_KIMI_API", "false").lower() == "true"
        self.kimi_key = os.getenv("KIMI_API_KEY")
        self.openai_key = os.getenv("OPENAI_API_KEY")

        # 🔍 DEBUG: Log what keys are available
        logger.info(f"USE_KIMI_API env: {os.getenv('USE_KIMI_API')}")
        logger.info(f"Using Kimi: {self.use_kimi}")
        logger.info(f"Kimi key present: {bool(self.kimi_key)}")
        logger.info(f"OpenAI key present: {bool(self.openai_key)}")

        if self.use_kimi:
            if not self.kimi_key:
                logger.error("KIMI_API_KEY not found in environment!")
            # ✅ use Kimi base URL
            self.client = OpenAI(
                api_key=self.kimi_key,
                base_url="https://api.moonshot.ai/v1"
            )
            self.model = "kimi-k2-0905-preview"
            logger.info(f"Initialized Kimi client with model: {self.model}")
        else:
            if not self.openai_key:
                logger.error("OPENAI_API_KEY not found in environment!")
            # fallback to OpenAI
            self.client = OpenAI(api_key=self.openai_key)
            self.model = "gpt-4o"
            logger.info(f"Initialized OpenAI client with model: {self.model}")

    def extract_fields(self, document_text: str):
        """Extract structured data (invoice_number, date, total_amount, vendor)."""
        prompt = f"""
        Extract the following fields from this document and return JSON only:
        - invoice_number
        - date
        - total_amount
        - vendor

        Document text:
        {document_text[:4000]}
        """

        try:
            logger.info(f"Calling LLM API with model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert document extraction assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            content = response.choices[0].message.content

            # 🧹 Clean fenced JSON if present
            if "```" in content:
                content = content.split("```")[-2]

            # 🛡️ JSON railguard starts here
            expected_keys = ["invoice_number", "date", "total_amount", "vendor"]

            try:
                parsed = json.loads(content.strip())
                clean = {k: parsed.get(k, None) for k in expected_keys}
                return clean
            except Exception as e:
                logger.error(f"JSON parse/validation failed: {e}")
                return {k: None for k in expected_keys}

        except Exception as e:
            # 🔍 Log the full exception details
            logger.error(f"LLM extraction failed: {e}", exc_info=True)
            return {"error": str(e)}