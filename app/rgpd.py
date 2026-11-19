import re
from datetime import datetime, timezone
from typing import Tuple
from app.models import RgpdAuditEvent

EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_RE = re.compile(r"(?:\+33|0)\s?[1-9](?:[\s.-]?\d{2}){4}\b")
NIR_RE = re.compile(r"\b[12]\s?\d{2}\s?\d{2}\s?\d{2}\s?\d{3}\s?\d{3}(?:\s?\d{2})?\b")


def sanitize_cv_for_llm(raw_text: str, source_label: str = "CV") -> Tuple[str, RgpdAuditEvent]:
    """Masque les données personnelles (PII) avant tout traitement IA/LLM (RGPD-by-Design)."""
    text, n_email = EMAIL_RE.subn("[EMAIL_MASQUÉ_RGPD]", raw_text)
    text, n_phone = PHONE_RE.subn("[TÉL_MASQUÉ_RGPD]", text)
    text, n_nir = NIR_RE.subn("[NIR_MASQUÉ_RGPD]", text)

    total = n_email + n_phone + n_nir
    event = RgpdAuditEvent(
        timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        action=f"Anonymisation PII ({source_label})",
        entities_redacted=total,
        details=f"{n_email} email(s), {n_phone} téléphone(s), {n_nir} NIR masqué(s) avant analyse IA.",
    )
    return text, event
