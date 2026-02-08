import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text_from_pdf(file_path: Path) -> str:
    """Extract text from PDF using PyMuPDF. Falls back to OCR for scanned pages."""
    import fitz

    doc = fitz.open(str(file_path))
    pages_text = []

    for page_num, page in enumerate(doc):
        text = page.get_text("text").strip()

        if len(text) < 20:
            text = _ocr_page(page, page_num)

        pages_text.append(text)

    doc.close()
    return "\n\n".join(pages_text).strip()


def extract_text_from_image(file_path: Path) -> str:
    """Extract text from an image file using Tesseract OCR."""
    try:
        import pytesseract
        from PIL import Image

        img = Image.open(file_path)
        return pytesseract.image_to_string(img).strip()
    except ImportError:
        logger.warning("pytesseract not installed — cannot OCR image %s", file_path)
        return ""
    except Exception as e:
        logger.error("OCR failed for image %s: %s", file_path, e)
        return ""


def _ocr_page(page, page_num: int) -> str:
    """OCR a single PDF page by rendering to image, then running Tesseract."""
    try:
        import pytesseract
        from PIL import Image
        import io

        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        text = pytesseract.image_to_string(img).strip()
        logger.info("OCR page %d: extracted %d chars", page_num, len(text))
        return text
    except ImportError:
        logger.warning("pytesseract not installed — skipping OCR for page %d", page_num)
        return ""
    except Exception as e:
        logger.error("OCR failed for page %d: %s", page_num, e)
        return ""


def extract_text(file_path: Path, mime_type: str) -> str:
    """Route to the correct extraction method based on MIME type."""
    if mime_type == "application/pdf":
        return extract_text_from_pdf(file_path)
    elif mime_type.startswith("image/"):
        return extract_text_from_image(file_path)
    else:
        logger.warning("Unsupported MIME type for text extraction: %s", mime_type)
        return ""
