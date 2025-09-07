import hashlib


def generate_rule_id(doc_id, section, text):
    """Generate a stable deterministic rule ID for a guideline."""
    base = f"{doc_id}|{section}|{text}".encode("utf-8")
    return hashlib.sha1(base).hexdigest()[:16]
