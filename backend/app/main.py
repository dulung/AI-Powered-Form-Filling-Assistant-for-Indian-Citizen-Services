from fastapi import FastAPI, File, UploadFile, Body
from fastapi.middleware.cors import CORSMiddleware
import re, cv2, numpy as np
from PIL import Image
import pytesseract
import logging
from rich.logging import RichHandler  # 👈 pretty
from difflib import get_close_matches
from typing import Dict
from pydantic import BaseModel

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("backend")

logger.info("🚀 Backend started — FormFill API running")

# --- FastAPI Setup ---
app = FastAPI(title="FormFill API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Image preprocessing helper ---
def preprocess_image_auto(file_bytes):
    """Try multiple preprocessing methods and return the best OCR text."""
    image_stream = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(image_stream, cv2.IMREAD_COLOR)
    if img is None:
        logger.error("❌ Image decode failed")
        return None, "Image decode failed"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    methods = {
        "gray": gray,
        "simple_thresh": cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1],
        "adaptive": cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C,
                                          cv2.THRESH_BINARY, 31, 15),
        "contrast": cv2.convertScaleAbs(gray, alpha=1.5, beta=0)
    }

    best_text = ""
    best_method = "gray"

    for name, img_proc in methods.items():
        try:
            text = pytesseract.image_to_string(img_proc)
            if len(text) > len(best_text):
                best_text = text
                best_method = name
        except Exception:
            pass

    return best_text, best_method


# --- Card Detection Helper ---
from .card_detector import detect_card_type

# --- Import Extractors ---
from .aadhar_extractor import extract_fields_from_text as extract_aadhar_fields
from .pan_extractor import extract_fields_from_text as extract_pan_fields
from .voter_extractor import extract_fields_from_text as extract_voter_fields


@app.post("/extract")
async def extract_fields(file: UploadFile = File(...)):
    contents = await file.read()
    text, method = preprocess_image_auto(contents)

    logger.info("\n===============================")
    logger.info(f"📸 OCR Method Used: {method}")
    logger.info("===============================")
    logger.info(f"OCR Extracted Text (first 500 chars):\n{text[:500]}")
    logger.info("===============================")

    if not text:
        logger.error("❌ OCR failed.")
        return {"error": "OCR failed"}

    # --- Detect card type ---
    card_type = detect_card_type(text)
    logger.info(f"🧩 Detected Card Type: {card_type}")

    # --- Route to extractor ---
    if card_type == "AADHAAR":
        logger.info("➡ Using Aadhaar extractor")
        fields = extract_aadhar_fields(text, file_bytes=contents)
    elif card_type == "PAN":
        logger.info("➡ Using PAN extractor")
        fields = extract_pan_fields(text, file_bytes=contents)
    elif card_type == "VOTER_ID":
        logger.info("➡ Using Voter ID extractor (to be implemented)")
        fields = extract_voter_fields(text, file_bytes=contents)
    else:
        logger.warning("⚠ Unknown or unsupported document type")
        fields = {"error": "Unknown or unsupported document type"}

    logger.info("\n✅ Final Extracted Fields:")
    for k, v in fields.items():
        logger.info(f"   {k}: {v}")

    return {
        "method_used": method,
        "card_type": card_type,
        "raw_text": text,
        "fields": fields
    }

# --- Import Template Mapper ---
from .template_mapper import map_fields_to_template

from typing import Dict, Optional, Union

class MappingRequest(BaseModel):
    template: str
    fields: Dict[str, Optional[Union[str, int, float]]]

# --- Final /map endpoint (only one active) ---
@app.post("/map")
async def map_fields(request: MappingRequest):
    logger.info("\n===============================")
    logger.info("🗺️  Incoming /map request")
    logger.info(f"Template requested: {request.template}")
    logger.info(f"Fields received: {list(request.fields.keys())}")
    logger.info("===============================")

    # Sanitize None → ""
    clean_fields = {k: (v if v is not None else "") for k, v in request.fields.items()}

    result = map_fields_to_template(request.template, clean_fields)

    logger.info(f"🧭 Mapping result for template '{request.template}':")
    logger.info(result)
    logger.info("===============================\n")

    return result
from fastapi.responses import FileResponse
import os

from fpdf import FPDF
from fastapi.responses import FileResponse

def ascii_safe(s):
    if not isinstance(s, str):
        s = str(s)
    s = s.replace('—', '-')
    return s.encode("latin1", "replace").decode("latin1")

@app.post("/generate-pdf")
async def generate_pdf(request: MappingRequest):
    logger.info(f"[PDF] Incoming /generate-pdf request with fields: {request.fields}")
    filled_path = "filled_form.pdf"

    pdf = FPDF()
    pdf.add_page()

    # Branding bar/top
    pdf.set_fill_color(232,240,253)
    pdf.rect(0, 0, 210, 16, style='F')
    pdf.set_font("Arial", "B", 16)
    pdf.set_text_color(67,108,255)
    pdf.cell(0, 12, ascii_safe("FormFill Assistant - Filled Form"), ln=True, align="C")
    pdf.ln(8)

    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Arial", size=13)

    # Details box
    pdf.set_xy(22, 30)
    pdf.cell(0, 10, ascii_safe("Extracted Information"), ln=True)
    pdf.ln(4)

    label_width = 45
    value_width = 95
    row = 0
    for k, v in request.fields.items():
        pretty = k.replace("_", " ").title()
        if row % 2 == 0:
            pdf.set_fill_color(250, 252, 255)
        else:
            pdf.set_fill_color(242, 244, 247)
        pdf.set_x(30)
        pdf.cell(label_width, 10, ascii_safe(f"{pretty}:"), 0, 0, "L", fill=True)
        pdf.cell(value_width, 10, ascii_safe(v if v else "-"), 0, 1, "L", fill=True)
        row += 1
    pdf.ln(10)

    # Footer/signature
    pdf.set_y(-30)
    pdf.set_font("Arial", "I", 11)
    pdf.set_text_color(110, 110, 110)
    pdf.cell(0, 10, ascii_safe("Generated by AI-Powered FormFill Assistant"), ln=True, align="C")

    pdf.output(filled_path)
    logger.info(f"[PDF] PDF generated and saved as {filled_path}")
    return FileResponse(
        filled_path,
        media_type="application/pdf",
        filename="filled_form.pdf"
    )