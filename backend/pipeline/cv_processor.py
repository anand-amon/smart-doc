from PIL import Image
import pytesseract
from pdf2image import convert_from_path
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class CVProcessor:
    def __init__(self):
        self.dpi = 300  # higher DPI → better OCR

    def pdf_to_images(self, pdf_path: Path):
        """Convert a PDF into a list of PIL images"""
        images = convert_from_path(pdf_path, dpi=self.dpi)
        logger.info(f"Converted {pdf_path.name} → {len(images)} page(s)")
        return images

    def preprocess_image(self, image: Image.Image):
        """Basic preprocessing before OCR"""
        if image.mode != "L":
            image = image.convert("L")  # grayscale
        return image

    def extract_text(self, image: Image.Image):
        """Run Tesseract OCR and compute average confidence"""
        processed = self.preprocess_image(image)
        ocr_data = pytesseract.image_to_data(processed, output_type=pytesseract.Output.DICT)
        text = pytesseract.image_to_string(processed)

        confs = [int(c) for c in ocr_data["conf"] if c != "-1"]
        avg_conf = sum(confs) / len(confs) if confs else 0
        return {"text": text, "confidence": avg_conf / 100}

    def process_document(self, file_path: Path):
        """Main entry point"""
        if file_path.suffix.lower() == ".pdf":
            images = self.pdf_to_images(file_path)
            image = images[0]  # first page only for now
        else:
            image = Image.open(file_path)

        result = self.extract_text(image)
        return {
            "file": file_path.name,
            "text": result["text"],
            "confidence": result["confidence"],
            "word_count": len(result["text"].split())
        }
