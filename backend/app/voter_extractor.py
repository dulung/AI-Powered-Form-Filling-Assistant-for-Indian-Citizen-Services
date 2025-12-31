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
logger = logging.getLogger("voter_extractor")

# Try to import EasyOCR (optional)
try:
    import easyocr
    EASYOCR_AVAILABLE = True
    _easyocr_reader = None
except ImportError:
    EASYOCR_AVAILABLE = False
    logger.warning("⚠️ EasyOCR not available. Install with: pip install easyocr")

def get_easyocr_reader():
    """Lazy load EasyOCR reader (initialized once)."""
    global _easyocr_reader
    if _easyocr_reader is None and EASYOCR_AVAILABLE:
        _easyocr_reader = easyocr.Reader(['en'], gpu=False)
    return _easyocr_reader

def extract_with_easyocr(file_bytes):
    """Extract text using EasyOCR - optimized for speed."""
    if not EASYOCR_AVAILABLE:
        return None
    try:
        reader = get_easyocr_reader()
        if reader is None:
            return None
        # Decode image
        image_stream = np.frombuffer(file_bytes, np.uint8)
        img = cv2.imdecode(image_stream, cv2.IMREAD_COLOR)
        if img is None:
            return None
        # Reduced scale for faster processing
        scale = 1.5
        img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        # Run EasyOCR
        results = reader.readtext(img)
        # Combine all detected text with confidence > 0.3
        text_parts = [text for (bbox, text, conf) in results if conf > 0.3]
        combined_text = "\n".join(text_parts)
        return combined_text
    except Exception as e:
        logger.warning(f"⚠️ EasyOCR extraction failed: {e}")
        return None

def extract_fields_from_text(text: str, file_bytes=None) -> dict:
    """
    Extract fields from Indian Voter ID card.
    Optimized hybrid approach: EasyOCR primary.
    """
    logger.info("\n🗳️ Starting Voter ID extraction...")
    fields = {
        "Name": None,
        "EPIC Number": None,
        "DOB": None,
        "Gender": None,
        "Relation Name": None,
        "Relation Type": None,
        "Address": None,
    }
    all_text = text
    if file_bytes:
        # --- EasyOCR extraction ---
        if EASYOCR_AVAILABLE:
            logger.info("🔍 Attempting EasyOCR extraction...")
            easyocr_text = extract_with_easyocr(file_bytes)
            if easyocr_text and len(easyocr_text.strip()) > 50:
                all_text = easyocr_text
                logger.info(f"✅ Using EasyOCR text ({len(all_text)} chars)")
                logger.info(f"📝 EasyOCR preview:\n{all_text[:300]}")
    if not all_text.strip():
        logger.warning("⚠️ No text available for extraction")
        return fields
    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
    logger.info(f"📄 Processing {len(lines)} lines")

    # --- EPIC Number ---
    epic_patterns = [
        r'\b([A-Z]{3}\d{7})\b',
        r'\b([A-Z]{2}\d{8})\b',
        r'([A-Z]{2,3}\s?\d{7,8})',
    ]
    text_clean = all_text.replace(" ", "").replace("\n", " ").upper()
    for pattern in epic_patterns:
        match = re.search(pattern, text_clean)
        if match:
            epic = match.group(1).replace(" ", "")
            if len(epic) in [10, 11]:
                fields["EPIC Number"] = epic
                logger.info(f"✅ EPIC Number: {epic}")
                break

    # --- Name (line-by-line approach) ---
    for i, line in enumerate(lines):
        # Look for standalone "Name" or common OCR errors
        if re.match(r'^\s*(Name|Mame|Nama)\s*$', line, re.IGNORECASE):
            # Name should be on next line
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                skip = ['election', 'commission', 'india', 'voter', 'epic', 
                        'father', 'mother', 'card', 'photo', 'identity']
                if not any(s in next_line.lower() for s in skip) and len(next_line) > 2:
                    fields["Name"] = next_line.title()
                    logger.info(f"✅ Name (below label): {next_line}")
                    break
        # Fallback: Inline "Name : VALUE" (but not "Father's" or "Mother's" Name)
        if re.search(r'\bName\s*[:\-]', line, re.IGNORECASE) and not re.search(r'(Father|Mother)', line, re.IGNORECASE):
            name_match = re.search(r'Name\s*[:\-]?\s*([A-Za-z][A-Za-z\s]{2,50})', line, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip()
                name = re.sub(r'\s+', ' ', name)
                skip = ['election', 'commission', 'india', 'voter', 'epic', 'card', 
                        'photo', 'identity', 'elector', 'father', 'mother']
                if not any(s in name.lower() for s in skip):
                    fields["Name"] = name.title()
                    logger.info(f"✅ Name (inline): {name}")
                    break

    # --- Father/Mother/Relation Extraction (new) ---
    if not fields["Relation Name"]:
        relation_patterns = [
            (r'Father[\'’s\s]*Name', "Father"),
            (r'Mother[\'’s\s]*Name', "Mother"),
            (r'Relation[\'’s\s]*Name', "Relation"),
        ]
        for rel_pat, rel_type in relation_patterns:
            for i, line in enumerate(lines):
                if re.search(rel_pat, line, re.IGNORECASE):
                    # Try to extract from same line first
                    same_line_match = re.search(r':\s*([A-Za-z\s]{2,40})', line)
                    name_val = None
                    if same_line_match:
                        name_val = same_line_match.group(1).strip()
                        # Optionally check next lines for surname extension
                        for j in range(1, 3):
                            if i + j < len(lines):
                                next_line = lines[i + j].strip()
                                if re.match(r'^[A-Za-z\s]{2,40}$', next_line):
                                    name_val += " " + next_line
                                else:
                                    break
                    else:
                        # Try the next line if not found on same line
                        if i + 1 < len(lines):
                            next_line = lines[i + 1].strip()
                            if re.match(r'^[A-Za-z\s]{2,40}$', next_line):
                                name_val = next_line
                    if name_val and len(name_val) > 2:
                        fields["Relation Name"] = name_val.title()
                        fields["Relation Type"] = rel_type
                        logger.info(f"✅ {rel_type}'s Name: {name_val}")
                        break
            if fields["Relation Name"]:
                break

    # --- DOB ---
    dob_patterns = [
        r'(?:DOB|Date\s*of\s*Birth)[:\s]*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})',
        r'\b(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4})\b',
    ]
    for pattern in dob_patterns:
        match = re.search(pattern, all_text, re.IGNORECASE)
        if match:
            fields["DOB"] = match.group(1).strip()
            logger.info(f"✅ DOB: {fields['DOB']}")
            break

    # --- Gender ---
    gender_match = re.search(r'\b(Male|Female|M|F)\b', all_text, re.IGNORECASE)
    if gender_match:
        gender = gender_match.group(1).upper()
        if gender in ['MALE', 'M']:
            fields["Gender"] = "Male"
        elif gender in ['FEMALE', 'F']:
            fields["Gender"] = "Female"
        if fields["Gender"]:
            logger.info(f"✅ Gender: {fields['Gender']}")

    # --- Address ---
    address_lines = []
    capture = False
    for line in lines:
        if any(kw in line.lower() for kw in ['address', 'c/o', 's/o']):
            capture = True
            addr_match = re.search(r'(?:address|पता)\s*[:\-]?\s*(.*)', line, re.IGNORECASE)
            if addr_match and len(addr_match.group(1).strip()) > 3:
                address_lines.append(addr_match.group(1).strip())
            continue
        if capture:
            if any(kw in line.lower() for kw in ['epic', 'election', 'age']):
                break
            if len(line) > 3:
                address_lines.append(line)
                if len(address_lines) >= 3:
                    break
    if address_lines:
        fields["Address"] = ', '.join(address_lines)
        logger.info(f"✅ Address: {fields['Address'][:60]}...")

    # --- Summary ---
    logger.info("\n🗳️ Voter ID Extraction Complete:")
    extracted_count = sum(1 for v in fields.values() if v)
    logger.info(f"   📊 Extracted {extracted_count}/{len(fields)} fields")
    for key, value in fields.items():
        if value:
            logger.info(f"   {key}: {value}")

    return fields