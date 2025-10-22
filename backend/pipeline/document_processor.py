from pathlib import Path
from backend.pipeline.cv_processor import CVProcessor
from backend.pipeline.llm_processor import LLMProcessor
import logging

logger = logging.getLogger("smartdoc")

class DocumentProcessor:
    def __init__(self):
        self.cv = CVProcessor()
        self.llm = LLMProcessor()

    def process(self, file_path: Path):
        logger.info(f"🟢 Starting document processing: {file_path}")

        try:
            # ---- OCR stage ----
            ocr_result = self.cv.process_document(file_path)
            logger.info(
                f"OCR complete for {file_path.name} | "
                f"Confidence={ocr_result.get('confidence', 0):.2f} | "
                f"Words={ocr_result.get('word_count', 0)}"
            )

            # ---- LLM stage ----
            llm_result = self.llm.extract_fields(ocr_result["text"])
            logger.info(f"LLM extraction complete for {file_path.name}")

            result = {
                "file": file_path.name,
                "ocr": {
                    "text": ocr_result["text"],
                    "confidence": ocr_result["confidence"],
                    "word_count": ocr_result["word_count"]
                },
                "extracted_data": llm_result
            }

            logger.info(f"✅ Finished processing {file_path.name}")
            return result

        except Exception as e:
            logger.error(f"❌ Processing failed for {file_path}: {e}", exc_info=True)
            return {"error": str(e)}