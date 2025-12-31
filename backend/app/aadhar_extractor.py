import re
import spacy
import cv2
import numpy as np
import pytesseract


# Load spaCy English model
nlp = spacy.load("en_core_web_sm")


def extract_fields_from_text(text: str, file_bytes=None):
    result = {
        "Name": None,
        "Father Name": None,
        "Mother Name": None,
        "DOB": None,
        "Gender": None,
        "PAN": None,
        "Aadhaar": None,
    }

    # --- Clean text but keep newlines intact ---
    cleaned = re.sub(r'[^A-Za-z0-9\n:/\-]', ' ', text)
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n+', '\n', cleaned).strip()
    lines = cleaned.split("\n")

    # --- Father's Name logic (unchanged) ---
    father_name = None
    candidates = []
    for i, line in enumerate(lines):
        if re.search(r'(Father|Fathe|Fathar|Fathcr|Fatner|Fatler|frrot|frther|Pita|Pitah|Husband)', line, re.IGNORECASE):
            candidates.append((i, line.strip()))
    
    chosen_line = None
    for _, line in candidates:
        if re.search(r'\bFather\b', line, re.IGNORECASE):
            chosen_line = line
            break
    
    if not chosen_line and candidates:
        for _, line in candidates:
            if re.search(r'\bFather\b', line, re.IGNORECASE):
                chosen_line = line
                break
    
    if chosen_line:
        m = re.search(r'Father\s*[:\-]?\s*([A-Za-z\s]{2,40})', chosen_line, re.IGNORECASE)
        if m:
            father_name = m.group(1).strip()
        else:
            idx = [i for i, l in candidates if l == chosen_line]
            if idx:
                i = idx[0]
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if re.match(r'^[A-Za-z\s]{3,40}$', next_line):
                        father_name = next_line
    
    if father_name:
        father_name = re.sub(
            r'\b(DOB|Date|Male|Gender|BWAO|fs|Ofs|fs4|BOA|S/D|W/O|D/O|Husband|Father)\b.*', '', father_name, flags=re.IGNORECASE
        )
        father_name = re.sub(r'\s{2,}', ' ', father_name).strip()
        result["Father Name"] = father_name

    # --- Mother's Name logic (same pattern as Father's Name) ---
    mother_name = None
    mother_candidates = []
    for i, line in enumerate(lines):
        if re.search(r'(Mother|Mothe|Mather|Mata|Mataji|Wife)', line, re.IGNORECASE):
            mother_candidates.append((i, line.strip()))
    
    chosen_mother_line = None
    for _, line in mother_candidates:
        if re.search(r'\bMother\b', line, re.IGNORECASE):
            chosen_mother_line = line
            break
    
    if not chosen_mother_line and mother_candidates:
        for _, line in mother_candidates:
            if re.search(r'\bMother\b', line, re.IGNORECASE):
                chosen_mother_line = line
                break
    
    if chosen_mother_line:
        m = re.search(r'Mother\s*[:\-]?\s*([A-Za-z\s]{2,40})', chosen_mother_line, re.IGNORECASE)
        if m:
            mother_name = m.group(1).strip()
        else:
            idx = [i for i, l in mother_candidates if l == chosen_mother_line]
            if idx:
                i = idx[0]
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if re.match(r'^[A-Za-z\s]{3,40}$', next_line):
                        mother_name = next_line
    
    if mother_name:
        mother_name = re.sub(
            r'\b(DOB|Date|Male|Gender|BWAO|fs|Ofs|fs4|BOA|S/D|W/O|D/O|Mother|Wife)\b.*', '', mother_name, flags=re.IGNORECASE
        )
        mother_name = re.sub(r'\s{2,}', ' ', mother_name).strip()
        result["Mother Name"] = mother_name

    # --- DOB extraction (unchanged) ---
    def extract_true_dob(cleaned_text):
        lines = cleaned_text.split("\n")
        for line in lines:
            if re.search(r'(DOB|Date\s*of\s*Birth)', line, re.IGNORECASE) and not re.search(r'issued|enrol|aadhaar', line, re.IGNORECASE):
                dob_match = re.search(r'(\d{2}[\/\-]\d{2}[\/\-]\d{4})', line)
                if dob_match:
                    return dob_match.group(1)
        for line in lines:
            if re.search(r'issued|enrol|aadhaar', line, re.IGNORECASE):
                continue
            dob_match = re.search(r'(\d{2}[\/\-]\d{2}[\/\-]\d{4})', line)
            if dob_match:
                return dob_match.group(1)
        return None

    result["DOB"] = extract_true_dob(cleaned)

    # --- Gender ---
    if re.search(r'\bMale\b', cleaned, re.IGNORECASE):
        result["Gender"] = "Male"
    elif re.search(r'\bFemale\b', cleaned, re.IGNORECASE):
        result["Gender"] = "Female"

    # --- 🆕 PRIMARY Name Extraction: Line BEFORE Father/Mother ---
    if not result["Name"]:
        for i, line in enumerate(lines):
            if re.search(r'\b(Father|Mother)\b', line, re.IGNORECASE):
                # Check previous line for name
                if i > 0:
                    prev_line = lines[i - 1].strip()
                    # Remove trailing colons/punctuation
                    prev_line = re.sub(r'[:\-\.\,]+ *$', '', prev_line).strip()
                    # Check if it's a name-like pattern (all caps or mixed, 5+ chars)
                    if re.match(r'^[A-Z][A-Za-z\s]{4,40}$', prev_line):
                        result["Name"] = prev_line
                        break

    # --- Name Extraction (fallback with spaCy) ---
    doc = nlp(cleaned)
    persons = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]

    if not result["Name"] and (result["Father Name"] or result["Mother Name"]):
        father_idx = cleaned.lower().find("father")
        husband_idx = cleaned.lower().find("husband")
        mother_idx = cleaned.lower().find("mother")
        
        # Find whichever comes first (father, husband, or mother)
        relation_idx = min([idx for idx in [father_idx, husband_idx, mother_idx] if idx != -1], default=-1)
        
        before_relation = cleaned[:relation_idx] if relation_idx != -1 else cleaned
        possible_names = [ent.text.strip() for ent in nlp(before_relation).ents if ent.label_ == "PERSON"]
        if possible_names:
            # Clean relationship keywords from extracted name
            name_candidate = possible_names[-1]
            name_candidate = re.sub(r'\b(Husband|Father|Wife|Son|Daughter|Mother)\b.*', '', name_candidate, flags=re.IGNORECASE).strip()
            result["Name"] = name_candidate if name_candidate else possible_names[-1]
        elif persons:
            # Clean relationship keywords from persons list
            cleaned_person = re.sub(r'\b(Husband|Father|Wife|Son|Daughter|Mother)\b.*', '', persons[0], flags=re.IGNORECASE).strip()
            result["Name"] = cleaned_person if cleaned_person else persons[0]
    elif not result["Name"] and persons:
        # Clean relationship keywords from persons list
        cleaned_person = re.sub(r'\b(Husband|Father|Wife|Son|Daughter|Mother)\b.*', '', persons[0], flags=re.IGNORECASE).strip()
        result["Name"] = cleaned_person if cleaned_person else persons[0]

    # --- Enhanced Name: handle bilingual Aadhaar and OCR variants ---
    if not result["Name"]:
        for i, line in enumerate(lines):
            if re.search(r'(Name)', line, re.IGNORECASE):
                # remove Hindi or slashes
                clean_line = re.sub(r'नाम\s*/\s*', '', line, flags=re.IGNORECASE)
                # now extract after Name, Name:, Name-, Name :
                m = re.search(r'Name\s*[:\-]?\s*([A-Za-z][A-Za-z\s\.]{2,40})', clean_line, re.IGNORECASE)
                if m:
                    possible_name = m.group(1).strip()
                    # Remove relationship keywords from name
                    possible_name = re.sub(r'\b(Husband|Father|Wife|Mother)\b.*', '', possible_name, flags=re.IGNORECASE).strip()
                    if len(possible_name.split()) >= 1:
                        result["Name"] = possible_name
                        break
                # FIX: If no name found after 'Name', try next line
                elif i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    # Aadhaar names can be single or multi-word
                    if re.match(r'^[A-Za-z][A-Za-z\s\.]{2,40}$', next_line):
                        result["Name"] = next_line
                        break

    # --- Fallback: Name directly above DOB or Gender ---
    if not result["Name"]:
        for i, line in enumerate(lines):
            if re.search(r'(DOB|Date\s*of\s*Birth|Male|Female)', line, re.IGNORECASE):
                if i > 0:
                    prev_line = lines[i - 1].strip()
                    if re.match(r'^[A-Z][a-z]+(?:\s[A-Z][a-z]+)*$', prev_line):
                        result["Name"] = prev_line
                        break

    # --- Final fallback: top 5 lines ---
    if not result["Name"]:
        for line in lines[:5]:
            if re.match(r'^[A-Z][a-z]+(?:\s[A-Z][a-z]+)*$', line):
                result["Name"] = line.strip()
                break

    # --- Aadhaar Recovery (bottom region OCR + full text scan) ---
    # First, try from bottom cropped region
    aadhaar_found = None
    if file_bytes:
        try:
            image_stream = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(image_stream, cv2.IMREAD_COLOR)
            h, w, _ = img.shape
            bottom_crop = img[int(h * 0.7):, :]
            gray = cv2.cvtColor(bottom_crop, cv2.COLOR_BGR2GRAY)
            gray = cv2.convertScaleAbs(gray, alpha=2, beta=0)
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            ocr_bottom = pytesseract.image_to_string(thresh)
            m = re.search(r'(\d{4}\s?\d{4}\s?\d{4})', ocr_bottom)
            if m:
                digits = re.sub(r'\D', '', m.group(1))
                if len(digits) == 12:
                    aadhaar_found = f"{digits[:4]} {digits[4:8]} {digits[8:]}"
        except Exception as e:
            print("Aadhaar OCR Error:", e)

    # If bottom scan failed, look in full text (for online Aadhaar layout)
    if not aadhaar_found:
        m = re.search(r'(\d{4}\s?\d{4}\s?\d{4})', cleaned)
        if m:
            digits = re.sub(r'\D', '', m.group(1))
            if len(digits) == 12:
                aadhaar_found = f"{digits[:4]} {digits[4:8]} {digits[8:]}"

    result["Aadhaar"] = aadhaar_found

    # --- Final fallback: Top name ---
    if not result["Name"]:
        for line in lines[:5]:
            if re.match(r'^[A-Z][a-z]+(?:\s[A-Z][a-z]+)+$', line):
                result["Name"] = line.strip()
                break

    return result