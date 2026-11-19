from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field


class ConsultantProfile(BaseModel):
    id: str
    pseudo_id: str
    full_name: str
    title: str
    years_exp: int
    skills: List[str]
    tjm_eur: int
    availability: Literal["Immédiate", "Sous 15j", "En mission (fin 30j)"]
    location: str
    summary: str
    experiences: List[str] = Field(default_factory=list)


class ClientNeed(BaseModel):
    id: str
    client_name: str
    sector: str
    title: str
    required_skills: List[str]
    min_years_exp: int
    max_tjm_eur: int
    location: str
    urgency: Literal["Haute", "Moyenne", "Basse"]
    contact_name: str
    contact_role: str
    source: Literal["BoondManager", "CRM", "M365_Email", "Appel_Offre"]


class MatchResult(BaseModel):
    need_id: str
    need_title: str
    client_name: str
    consultant_id: str
    consultant_name: str
    score: int = Field(ge=0, le=100)
    matched_skills: List[str]
    missing_skills: List[str]
    tjm_ok: bool
    rationale: str


class RgpdAuditEvent(BaseModel):
    timestamp: str
    action: str
    entities_redacted: int
    details: str


class DossierCompetences(BaseModel):
    consultant_id: str
    consultant_name: str
    target_need: str
    markdown: str


class ProspectionCampaign(BaseModel):
    need_id: str
    client_name: str
    contact_name: str
    subject: str
    email_body: str
    linkedin_dm: str


class WeeklyKpis(BaseModel):
    cvs_processed: int
    rgpd_pii_masked: int
    active_needs: int
    qualified_matches: int
    avg_match_score: float
    dossiers_generated: int
    campaigns_ready: int
    estimated_hours_saved: float
    connector_status: Dict[str, str]


class E2EPipelineResponse(BaseModel):
    mode: Literal["gemini_live", "deterministic_engine"]
    kpis: WeeklyKpis
    matches: List[MatchResult]
    rgpd_events: List[RgpdAuditEvent]
    sample_dossier: Optional[DossierCompetences] = None
    sample_campaign: Optional[ProspectionCampaign] = None
