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
        if file_path.suffix.lower() == ".pdf":
            images = self.pdf_to_images(file_path)
        else:
            images = [Image.open(file_path)]

        all_text = []
        confs = []
        word_count = 0

        for image in images:
            ocr = self.extract_text(image)
            all_text.append(ocr["text"])
            confs.append(ocr["confidence"])
            word_count += len(ocr["text"].split())

        text = "\n".join(all_text)
        avg_conf = sum(confs) / len(confs) if confs else 0

        logger.info(f"OCR average confidence: {avg_conf:.2f}")
        
        return {
            "file": file_path.name,
            "text": text,
            "confidence": avg_conf,
            "word_count": word_count
        }
