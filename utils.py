import fitz
import io
import pytesseract
import base64
from PIL import Image
from docx import Document

def extract_pdf(file_bytes):
    document = fitz.open(stream=file_bytes, filetype="pdf")
    return "\n".join([page.get_text() for page in document])

def extract_docx(file_bytes):
    document = Document(io.BytesIO(file_bytes))
    return "\n".join([paragraph.text for paragraph in document.paragraphs])

def extract_image(file_bytes):
    image = Image.open(io.BytesIO(file_bytes))
    return pytesseract.image_to_string(image)

def extract_text_from_file(file_bytes, filename):
    ext = filename.lower().split('.')[-1]
    if ext == "pdf":
        return extract_pdf(file_bytes)
    elif ext == "docx":
        return extract_docx(file_bytes)
    elif ext in ("png", "jpg", "jpeg"):
        return extract_image(file_bytes)
    else:
        raise ValueError(f"Unsupported file type: {filename}")

def image_to_base64(file_bytes):
    return base64.b64encode(file_bytes).decode("utf-8")