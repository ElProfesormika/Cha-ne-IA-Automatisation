import io
import os
from pathlib import Path
from typing import Dict, Any, List

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pypdf import PdfReader

from app.connectors import ToolsConnectorHub
from app.models import (
    ClientNeed,
    ConsultantProfile,
    E2EPipelineResponse,
    WeeklyKpis,
)
from app.pipeline import (
    generate_dossier_competences,
    generate_prospection_campaign,
    match_consultants_to_needs,
    parse_and_score_cv,
)
from app.rgpd import sanitize_cv_for_llm
from data.sample_data import SAMPLE_CV_TEXT

load_dotenv()

app = FastAPI(
    title="NEOSIA AI & Automation Pipeline",
    description="Chaîne automatisée de bout en bout : Sourcing CV RGPD -> Matching -> Dossier de Compétences -> Prospection -> Dashboard",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

hub = ToolsConnectorHub()


def _fresh_state() -> Dict[str, Any]:
    return {
        "consultants": hub.fetch_boond_consultants(),
        "needs": hub.fetch_market_needs(),
        "rgpd_events": [],
        "dossiers_generated": 3,
        "campaigns_ready": 3,
    }


STATE: Dict[str, Any] = _fresh_state()


class RawCvRequest(BaseModel):
    filename: str = "cv_candidat.txt"
    content: str


class WebhookPayload(BaseModel):
    event: str = "new_client_need"
    client_name: str
    title: str
    required_skills: List[str]
    max_tjm_eur: int = 600
    min_years_exp: int = 3
    location: str = "Toulouse"
    contact_name: str = "Direction Technique"
    contact_role: str = "Décideur"
    source: str = "CRM"


class PairRequest(BaseModel):
    consultant_id: str
    need_id: str


@app.get("/api/health")
def health():
    has_key = bool(os.getenv("GEMINI_API_KEY", "").strip())
    return {
        "status": "ok",
        "project": "NEOSIA AI & Automation",
        "mode": "gemini_live" if has_key else "deterministic_engine",
        "connectors": hub.get_connector_statuses(),
    }


@app.get("/api/state")
def get_state():
    return {
        "consultants": STATE["consultants"],
        "needs": STATE["needs"],
        "rgpd_events": STATE["rgpd_events"],
    }


@app.post("/api/reset")
def reset_demo():
    global STATE
    STATE = _fresh_state()
    return {"status": "reset_ok"}


@app.get("/api/sample-cv")
def get_sample_cv():
    return {"filename": "CV_Camille_Lefevre_IA.txt", "content": SAMPLE_CV_TEXT.strip()}


@app.post("/api/cv/parse")
def parse_cv_text(req: RawCvRequest):
    sanitized_preview, _ = sanitize_cv_for_llm(req.content, req.filename)
    profile, rgpd_event = parse_and_score_cv(req.content, req.filename)
    if not any(c.id == profile.id for c in STATE["consultants"]):
        STATE["consultants"].insert(0, profile)
    STATE["rgpd_events"].insert(0, rgpd_event)
    return {
        "profile": profile,
        "rgpd_event": rgpd_event,
        "original_preview": req.content,
        "sanitized_preview": sanitized_preview,
    }


@app.post("/api/cv/upload")
async def upload_cv_file(file: UploadFile = File(...)):
    raw = await file.read()
    filename = file.filename or "cv.txt"
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(raw))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    else:
        text = raw.decode("utf-8", errors="replace")
    sanitized_preview, _ = sanitize_cv_for_llm(text, filename)
    profile, rgpd_event = parse_and_score_cv(text, filename)
    if not any(c.id == profile.id for c in STATE["consultants"]):
        STATE["consultants"].insert(0, profile)
    STATE["rgpd_events"].insert(0, rgpd_event)
    return {
        "profile": profile,
        "rgpd_event": rgpd_event,
        "original_preview": text,
        "sanitized_preview": sanitized_preview,
    }


@app.post("/api/needs")
@app.post("/api/webhooks/n8n")
def receive_n8n_or_make_webhook(payload: WebhookPayload):
    """Ajoute un besoin client depuis l'UI ou via webhook n8n / Make / Power Automate."""
    allowed_sources = {"BoondManager", "CRM", "M365_Email", "Appel_Offre"}
    src = payload.source if payload.source in allowed_sources else "CRM"
    new_need = ClientNeed(
        id=f"NEED-{len(STATE['needs']) + 101}",
        client_name=payload.client_name,
        sector="Tech / Conseil",
        title=payload.title,
        required_skills=payload.required_skills,
        min_years_exp=payload.min_years_exp,
        max_tjm_eur=payload.max_tjm_eur,
        location=payload.location,
        urgency="Haute",
        contact_name=payload.contact_name,
        contact_role=payload.contact_role,
        source=src,
    )
    STATE["needs"].insert(0, new_need)
    return {"status": "need_ingested", "need": new_need}


@app.post("/api/dossier")
def generate_dossier_for_pair(req: PairRequest):
    c_obj = next((c for c in STATE["consultants"] if c.id == req.consultant_id), None)
    n_obj = next((n for n in STATE["needs"] if n.id == req.need_id), None)
    if not c_obj or not n_obj:
        raise HTTPException(status_code=404, detail="Consultant ou besoin introuvable")
    STATE["dossiers_generated"] += 1
    return generate_dossier_competences(c_obj, n_obj)


@app.post("/api/prospection")
def generate_prospection_for_pair(req: PairRequest):
    c_obj = next((c for c in STATE["consultants"] if c.id == req.consultant_id), None)
    n_obj = next((n for n in STATE["needs"] if n.id == req.need_id), None)
    if not c_obj or not n_obj:
        raise HTTPException(status_code=404, detail="Consultant ou besoin introuvable")
    match = match_consultants_to_needs([c_obj], [n_obj])[0]
    STATE["campaigns_ready"] += 1
    return generate_prospection_campaign(n_obj, match)


@app.post("/api/run-e2e", response_model=E2EPipelineResponse)
def run_end_to_end_pipeline():
    """Exécute la chaîne complète : Vivier + Besoins -> Matching -> Dossier -> Prospection -> KPIs."""
    consultants: List[ConsultantProfile] = STATE["consultants"]
    needs: List[ClientNeed] = STATE["needs"]

    matches = match_consultants_to_needs(consultants, needs)
    qualified = [m for m in matches if m.score >= 65]
    top_match = matches[0] if matches else None

    sample_dossier = None
    sample_campaign = None
    if top_match:
        c_obj = next(c for c in consultants if c.id == top_match.consultant_id)
        n_obj = next(n for n in needs if n.id == top_match.need_id)
        sample_dossier = generate_dossier_competences(c_obj, n_obj)
        sample_campaign = generate_prospection_campaign(n_obj, top_match)
        hub.trigger_automation_webhook(
            {
                "event": "top_match_ready",
                "client": n_obj.client_name,
                "consultant_pseudo": c_obj.pseudo_id,
                "score": top_match.score,
            }
        )

    pii_total = sum(e.entities_redacted for e in STATE["rgpd_events"])
    avg_score = round(sum(m.score for m in qualified) / max(len(qualified), 1), 1)
    hours_saved = round(
        len(consultants) * 0.4
        + STATE["dossiers_generated"] * 1.2
        + STATE["campaigns_ready"] * 0.5,
        1,
    )

    kpis = WeeklyKpis(
        cvs_processed=len(consultants),
        rgpd_pii_masked=pii_total,
        active_needs=len(needs),
        qualified_matches=len(qualified),
        avg_match_score=avg_score,
        dossiers_generated=STATE["dossiers_generated"],
        campaigns_ready=STATE["campaigns_ready"],
        estimated_hours_saved=hours_saved,
        connector_status=hub.get_connector_statuses(),
    )

    has_key = bool(os.getenv("GEMINI_API_KEY", "").strip())
    return E2EPipelineResponse(
        mode="gemini_live" if has_key else "deterministic_engine",
        kpis=kpis,
        matches=matches[:12],
        rgpd_events=STATE["rgpd_events"],
        sample_dossier=sample_dossier,
        sample_campaign=sample_campaign,
    )


@app.get("/")
def serve_dashboard():
    index_path = Path(__file__).parent.parent / "static" / "index.html"
    return FileResponse(index_path)
