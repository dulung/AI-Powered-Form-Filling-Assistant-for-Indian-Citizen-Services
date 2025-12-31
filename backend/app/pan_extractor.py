import re
import logging
from rich.logging import RichHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)
logger = logging.getLogger("pan_extractor")


def extract_fields_from_text(text: str, file_bytes=None):
    result = {
        "Name": None,
        "Father Name": None,
        "DOB": None,
        "Gender": None,
        "PAN": None,
        "Aadhaar": None,
    }

    # --- Clean up text ---
    cleaned = re.sub(r'[^A-Za-z0-9\n:/\-]', ' ', text)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n+', '\n', cleaned).strip()
    lines = [line.strip() for line in cleaned.split('\n') if line.strip()]

    logger.info("\n=== OCR CLEANED LINES ===")
    for i, line in enumerate(lines):
        logger.info(f"{i}: {line}")

    # --- PAN Number ---
    pan_match = re.search(r'([A-Z]{5}[0-9]{4}[A-Z])', text.replace(" ", "").upper())
    if pan_match:
        result["PAN"] = pan_match.group(1).upper()
        logger.info(f"✅ PAN Number Detected: {result['PAN']}")

    # --- DOB ---
    dob_match = re.search(r'(\d{2}[\/\-]\d{2}[\/\-]\d{4})', text)
    if dob_match:
        result["DOB"] = dob_match.group(1)
        logger.info(f"✅ DOB Detected: {result['DOB']}")

    # --- Extract Name and Father's Name ---
    name_line, fname_line = None, None

    for i, line in enumerate(lines):
        # 1️⃣ Find "Name" label (but not "Father's Name")
        if re.search(r'\bName\b', line, re.IGNORECASE) and not re.search(r"Father", line, re.IGNORECASE):
            for j in range(i+1, min(i+3, len(lines))):
                candidate = lines[j].strip()
                # Clean prefixes like "a " or "* "
                candidate_cleaned = re.sub(r'^[a-z]\s+', '', candidate)
                candidate_cleaned = re.sub(r'^\*\s+', '', candidate_cleaned)
                
                # Must be mostly uppercase alphabetic (allow spaces) AND not GOVT/INDIA
                if (re.match(r'^[A-Z\s]{3,}$', candidate_cleaned) 
                    and "NAME" not in candidate_cleaned
                    and "GOVT" not in candidate_cleaned
                    and "INDIA" not in candidate_cleaned):
                    name_line = candidate_cleaned
                    logger.info(f"✅ Detected Name line: '{candidate_cleaned}'")
                    break

        # 2️⃣ Find "Father's Name"
        if re.search(r"Father", line, re.IGNORECASE):
            for j in range(i+1, min(i+3, len(lines))):
                candidate = lines[j].strip()
                # Clean prefixes
                candidate_cleaned = re.sub(r'^[a-z]\s+', '', candidate)
                candidate_cleaned = re.sub(r'^\*\s+', '', candidate_cleaned)
                
                # 🆕 FIX: Also check if line has mostly alphabetic chars (even if lowercase)
                # Convert to uppercase for pattern matching
                candidate_upper = candidate_cleaned.upper()
                
                # Check if it matches name pattern after uppercase conversion
                if (re.match(r'^[A-Z\s]{3,}$', candidate_upper) 
                    and "NAME" not in candidate_upper
                    and len(candidate_cleaned.split()) >= 1):  # At least one word
                    # Use the uppercase version as father's name
                    fname_line = candidate_upper
                    logger.info(f"✅ Detected Father's Name line: '{fname_line}'")
                    break

    # --- Fallback Logic ---
    if not name_line or not fname_line:
        uppercase_name_candidates = []
        
        for i, line in enumerate(lines):
            # Clean prefixes
            cleaned_line = re.sub(r'^[a-z]\s+', '', line)
            cleaned_line = re.sub(r'^\*\s+', '', cleaned_line)
            
            # Remove trailing numbers and spaces
            cleaned_line = re.sub(r'\s+\d+\s*$', '', cleaned_line).strip()
            
            # Remove trailing lowercase words (OCR noise like "ose")
            cleaned_line = re.sub(r'\s+[a-z]+\s*$', '', cleaned_line).strip()
            
            # Allow single-letter initials
            pattern_match = re.match(r'^[A-Z]{1,}(\s+[A-Z]+)*$', cleaned_line)
            
            # Match: All caps, minimum length 3 total, no noise keywords
            if (pattern_match
                and "NAME" not in cleaned_line 
                and "ACCOUNT" not in cleaned_line
                and "INCOME" not in cleaned_line
                and "DEPARTMENT" not in cleaned_line
                and "GOVT" not in cleaned_line
                and "GOVERNMENT" not in cleaned_line
                and "INDIA" not in cleaned_line
                and "PERMANENT" not in cleaned_line
                and "SIGNATURE" not in cleaned_line
                and len(cleaned_line) >= 3):
                uppercase_name_candidates.append(cleaned_line)
                logger.info(f"🔍 Candidate name found: '{cleaned_line}'")

        # Assign first candidate to Name, second to Father's Name
        if not name_line and len(uppercase_name_candidates) >= 1:
            name_line = uppercase_name_candidates[0]
            logger.info(f"⚙ Fallback Name Detected: '{name_line}'")
        
        if not fname_line and len(uppercase_name_candidates) >= 2:
            fname_line = uppercase_name_candidates[1]
            logger.info(f"⚙ Fallback Father's Name Detected: '{fname_line}'")
        
        # Only combine if BOTH are short single-word or initials
        if len(uppercase_name_candidates) >= 2:
            first = uppercase_name_candidates[0]
            second = uppercase_name_candidates[1]
            
            # Check if first is a single letter or very short (initial)
            first_is_initial = len(first.split()) == 1 and len(first) <= 2
            # Check if first line has only 1-2 words with at least one being short
            first_words = first.split()
            first_is_short = len(first_words) <= 2 and any(len(w) <= 2 for w in first_words)
            
            # Only combine if first line looks like an initial/short name
            if first_is_short or first_is_initial:
                if len(second.split()) <= 2:
                    combined_name = f"{first} {second}"
                    logger.info(f"💡 Combining short lines into full name: '{combined_name}'")
                    name_line = combined_name
                    fname_line = None
                    logger.info(f"⚙ Combined name, no father name available")

    # --- Assign Values ---
    result["Name"] = name_line
    result["Father Name"] = fname_line

    logger.info("\n=== FINAL EXTRACTED FIELDS ===")
    for k, v in result.items():
        logger.info(f"{k}: {v}")

    return result