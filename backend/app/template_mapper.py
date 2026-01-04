import json
import os
import logging
from difflib import get_close_matches

logger = logging.getLogger("template_mapper")

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

def map_fields_to_template(template_name: str, extracted_fields: dict):
    """
    Maps OCR extracted fields to official form fields based on the template JSON.
    Adds detailed debug logging for troubleshooting.
    """

    logger.info("\n================ TEMPLATE MAPPING START ================")
    logger.info(f"🔹 Received template_name: {template_name}")
    logger.info(f"🔹 Available templates dir: {TEMPLATE_DIR}")
    logger.info(f"🔹 Extracted field keys: {list(extracted_fields.keys())}")

    if not template_name:
        logger.error("❌ Missing template_name in request")
        return {"error": "Invalid or missing template name"}

    # Check if template directory exists
    if not os.path.exists(TEMPLATE_DIR):
        logger.error(f"❌ Template directory not found at path: {TEMPLATE_DIR}")
        return {"error": f"Template directory not found at {TEMPLATE_DIR}"}

    template_path = os.path.join(TEMPLATE_DIR, f"{template_name}.json")
    logger.info(f"📂 Expected template path: {template_path}")

    if not os.path.exists(template_path):
        logger.error(f"❌ Template file not found: {template_path}")
        return {"error": f"Template '{template_name}' not found in {TEMPLATE_DIR}"}

    # Try reading the template file
    try:
        with open(template_path, "r", encoding="utf-8") as f:
            template = json.load(f)
            mapping = template.get("mapping", {})

    except Exception as e:
        logger.exception(f"❌ Failed to load template JSON: {e}")
        return {"error": f"Error loading template file: {str(e)}"}

    mapped_fields = {}

    for official_field, possible_keys in mapping.items():
        matched_value = ""

        # Try exact match first
        for key in possible_keys:
            if key in extracted_fields and extracted_fields[key]:
                matched_value = extracted_fields[key]
                logger.info(f"✅ Exact match: {official_field} ← {key}")
                break

        # If not found, try fuzzy match
        if not matched_value:
            for key in possible_keys:
                close = get_close_matches(key, extracted_fields.keys(), n=1, cutoff=0.65)
                if close:
                    matched_value = extracted_fields[close[0]]
                    logger.info(f"🔸 Fuzzy match: {official_field} ← {close[0]} (for {key})")
                    break

        mapped_fields[official_field] = matched_value

    logger.info(f"✅ Mapping complete for template: {template_name}")
    for k, v in mapped_fields.items():
        logger.info(f"   {k}: {v}")

    logger.info("================ TEMPLATE MAPPING END ================\n")

    return {"template": template_name, "mapped_fields": mapped_fields}