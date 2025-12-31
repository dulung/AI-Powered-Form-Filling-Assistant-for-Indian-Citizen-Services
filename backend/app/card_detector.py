import re
import cv2
import numpy as np
import pytesseract
import logging
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("card_detector")

# EasyOCR setup (optional)
try:
    import easyocr
    EASYOCR_AVAILABLE = True
    _easyocr_reader = None
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("⚠️ EasyOCR not available. Install with: pip install easyocr")

def get_easyocr_reader():
    global _easyocr_reader
    if _easyocr_reader is None and EASYOCR_AVAILABLE:
        _easyocr_reader = easyocr.Reader(['en', 'hi'], gpu=False)
    return _easyocr_reader

def extract_with_easyocr(file_bytes):
    if not EASYOCR_AVAILABLE:
        return None
    try:
        reader = get_easyocr_reader()
        if reader is None:
            return None
        image_stream = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(image_stream, cv2.IMREAD_COLOR)
        if img is None:
            return None
        scale = 1.5
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        results = reader.readtext(img)
        text_parts = [text for (bbox, text, conf) in results if conf > 0.3]
        combined_text = "\n".join(text_parts)
        return combined_text
    except Exception as e:
        logger.warning(f"⚠️ EasyOCR extraction failed: {e}")
        return None

# --- Best multi-path OCR for difficult images ---
def preprocess_for_ocr(img):
    kernel = np.array([[0,-1,0], [-1,5,-1], [0,-1,0]])
    sharp = cv2.filter2D(img, -1, kernel)
    denoise = cv2.bilateralFilter(sharp, 9, 75, 75)
    thresh = cv2.adaptiveThreshold(cv2.cvtColor(denoise, cv2.COLOR_BGR2GRAY), 255,
                                  cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
    return thresh

def run_all_ocr_methods(image_bytes):
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
    results = []
    if EASYOCR_AVAILABLE:
        text_ez = extract_with_easyocr(image_bytes)
        if text_ez and len(text_ez) > 10:
            results.append(('EasyOCR', text_ez))
        if img is not None:
            sharpened = preprocess_for_ocr(img)
            sharpened_bytes = cv2.imencode('.jpg', sharpened)[1].tobytes()
            text_ez_sharp = extract_with_easyocr(sharpened_bytes)
            if text_ez_sharp and len(text_ez_sharp) > 10:
                results.append(('EasyOCR-Sharp', text_ez_sharp))
    thresh = cv2.adaptiveThreshold(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY), 255,
                                  cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 2)
    text_tess = pytesseract.image_to_string(thresh, lang='eng+hin')
    if text_tess and len(text_tess) > 10:
        results.append(('Tesseract-Adapt', text_tess))
    sharp_img = preprocess_for_ocr(img)
    text_tess_sharp = pytesseract.image_to_string(sharp_img, lang='eng+hin')
    if text_tess_sharp and len(text_tess_sharp) > 10:
        results.append(('Tesseract-Sharp', text_tess_sharp))
    best = max(results, key=lambda tup: sum(c.isalnum() for c in tup[1]), default=('', ''))
    return best[1]

def extract_and_detect_card_type(image_bytes):
    best_text = run_all_ocr_methods(image_bytes)
    card_type = detect_card_type(best_text)
    return card_type, best_text

def detect_card_type(text: str) -> str:
    if not text or not text.strip():
        logger.warning("⚠ Empty OCR text — cannot detect card type.")
        return "UNKNOWN"
    cleaned = text.lower()
    logger.info("\n--- CARD DETECTOR DEBUG LOG ---")
    logger.info(f"OCR Preview (first 200 chars):\n{cleaned[:200]}...")
    logger.info("--------------------------------")
    # --- PAN CARD DETECTION (highest priority) ---
    pan_patterns = [
        r'income\s*tax\s*department',
        r'permanent\s*account\s*number',
    ]
    pan_number_pattern = r'[A-Z]{5}[0-9]{4}[A-Z]'
    found_pan_keyword = any(re.search(p, text, re.IGNORECASE) for p in pan_patterns)
    pan_match = re.search(pan_number_pattern, text.replace(" ", "").upper())
    if found_pan_keyword or pan_match:
        logger.info("✅ Classified as: PAN")
        return "PAN"
    # --- VOTER ID DETECTION ---
    voter_keywords = [
        "election commission",
        "voter id",
        "epic",
        "nirvachan ayog",
        "निर्वाचन आयोग"
    ]
    if any(keyword in cleaned for keyword in voter_keywords):
        logger.info("✅ Classified as: VOTER_ID")
        return "VOTER_ID"
    # --- AADHAAR CARD DETECTION ---
    aadhaar_patterns = [
        r'\buidai\b',
        r'\baad+haar\b',
        r'\bad+har\b',
        r'\bunique\s+identification\s+authority\b',
        r'\bgovernment\s+of\s+india\b',
        r'\bgovt\.?\s*of\s*india\b',
        r'आधार',
        r'\bmother\b',
        r'\bfather\b',
    ]
    aadhaar_number_pattern = r'\b\d{4}\s?\d{4}\s?\d{4}\b'
    found_aadhaar_keyword = any(re.search(p, cleaned) for p in aadhaar_patterns)
    aadhaar_match = re.search(aadhaar_number_pattern, cleaned)
    if found_aadhaar_keyword or aadhaar_match:
        logger.info("✅ Classified as: AADHAAR")
        return "AADHAAR"
    logger.warning("⚠ Could not detect card type — returning UNKNOWN")
    return "UNKNOWN"