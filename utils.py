# utils.py
import fitz
import io
import pytesseract
import base64
import logging
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
    return "\n\n".join([paragraph.text for paragraph in document.paragraphs]).strip()


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
    
    if ext == "pdf":
        return extract_pdf(file_bytes)
    elif ext == "docx":
        return extract_docx(file_bytes)
    elif ext in ("png", "jpg", "jpeg"):
        return extract_image(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}. "
                        "Supported formats: .pdf, .docx, .png, .jpg, .jpeg")


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
            logger.info(f"Resizing image from {w}x{h} to {new_size}")
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