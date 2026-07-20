# utils.py
import fitz
import io
import pytesseract
import base64
import logging
import re
from PIL import Image
from docx import Document

logger = logging.getLogger(__name__)

MAX_IMAGE_DIMENSION = 2048  # Resize large images before base64 encoding for API


def extract_pdf(file_bytes: bytes) -> str:
    """Extract text from a PDF file using PyMuPDF.

    Args:
        file_bytes: Raw PDF file bytes.

    Returns:
        Concatenated text from all pages.
    """
    document = fitz.open(stream=file_bytes, filetype="pdf")
    try:
        text_pages = [page.get_text() for page in document]
        return "\n\n".join(text_pages).strip()
    finally:
        document.close()


def extract_docx(file_bytes: bytes) -> str:
    """Extract text from a DOCX file.

    Args:
        file_bytes: Raw DOCX file bytes.

    Returns:
        Concatenated paragraph text.
    """
    document = Document(io.BytesIO(file_bytes))
    try:
        return "\n\n".join([paragraph.text for paragraph in document.paragraphs]).strip()
    finally:
        document.close()


def extract_image(file_bytes: bytes) -> str:
    """Extract text from an image using Tesseract OCR.

    Args:
        file_bytes: Raw image file bytes.

    Returns:
        Extracted text string.
    """
    image = Image.open(io.BytesIO(file_bytes))
    try:
        # Optional: enhance image for better OCR
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        return pytesseract.image_to_string(image).strip()
    finally:
        image.close()


def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Route file extraction based on extension.

    Args:
        file_bytes: Raw file bytes.
        filename: Original filename with extension.

    Returns:
        Extracted text content.

    Raises:
        ValueError: If the file type is unsupported.
    """
    if not filename:
        raise ValueError("No filename provided.")

    ext = filename.lower().split(".")[-1]

    try:
        if ext == "pdf":
            return extract_pdf(file_bytes)
        elif ext == "docx":
            return extract_docx(file_bytes)
        elif ext in ("png", "jpg", "jpeg"):
            return extract_image(file_bytes)
        else:
            raise ValueError(f"Unsupported file type: {filename}. "
                            "Supported formats: .pdf, .docx, .png, .jpg, .jpeg")
    except Exception as exc:
        logger.error("Failed to extract text from %s: %s", filename, exc)
        raise


def image_to_base64(file_bytes: bytes) -> str:
    """Encode image bytes to base64, resizing if too large.

    Args:
        file_bytes: Raw image file bytes.

    Returns:
        Base64-encoded string of the (possibly resized) image.
    """
    image = Image.open(io.BytesIO(file_bytes))
    try:
        # Resize if any dimension exceeds MAX_IMAGE_DIMENSION
        w, h = image.size
        if max(w, h) > MAX_IMAGE_DIMENSION:
            ratio = MAX_IMAGE_DIMENSION / max(w, h)
            new_size = (int(w * ratio), int(h * ratio))
            logger.info("Resizing image from %dx%d to %s", w, h, new_size)
            image = image.resize(new_size, Image.LANCZOS)

        # Convert to RGB if necessary (e.g., RGBA or P mode)
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")

        buf = io.BytesIO()
        image.save(buf, format="JPEG", quality=85, optimize=True)
        buf.seek(0)
        return base64.b64encode(buf.read()).decode("utf-8")
    finally:
        image.close()


def extract_grade(text: str) -> str:
    """Extract a grade string from AI-generated text using regex patterns.

    Supports formats like: X/10, Grade: A, X/100, X/20, X/50

    Args:
        text: The AI response text to parse.

    Returns:
        The extracted grade string, or "N/A" if no pattern matches.
    """
    if not text:
        return "N/A"
    patterns = [
        r"\b(\d{1,2}(?:\.\d+)?)\s*/\s*10\b",
        r"\bGrade[:\s]*([A-F][+-]?)\b",
        r"\b(\d{1,2}(?:\.\d+)?)\s*/\s*(?:100|20|50)\b",
    ]
    for pat in patterns:
        m = re.search(pat, text, re.I)
        if m:
            if "Grade" in pat:
                return m.group(1)
            return m.group(0).replace(" ", "")
    return "N/A"