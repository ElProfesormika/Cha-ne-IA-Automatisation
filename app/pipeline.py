import json
import os
import re
from typing import List, Tuple
import httpx

from app.models import (
    ClientNeed,
    ConsultantProfile,
    DossierCompetences,
    MatchResult,
    ProspectionCampaign,
    RgpdAuditEvent,
)
from app.rgpd import sanitize_cv_for_llm

KNOWN_SKILLS = [
    "Python", "FastAPI", "LLM", "Gemini", "Vertex AI", "LangChain", "RAG",
    "Docker", "Kubernetes", "GCP", "Azure", "SQL", "PostgreSQL", "Airflow",
    "dbt", "n8n", "Make", "Power Automate", "Microsoft 365", "CRM",
    "BoondManager", "Power BI", "APIs", "RGPD",
]


def _get_gemini_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def _call_gemini_text(prompt: str) -> str | None:
    api_key = _get_gemini_key()
    if not api_key:
        return None
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip() or "gemini-2.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    try:
        resp = httpx.post(
            url,
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=15.0,
        )
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return None


def parse_and_score_cv(
    raw_cv_text: str, filename: str = "cv_import.txt"
) -> Tuple[ConsultantProfile, RgpdAuditEvent]:
    """Trie et structure un CV après anonymisation RGPD."""
    sanitized_text, rgpd_event = sanitize_cv_for_llm(raw_cv_text, source_label=filename)

    lines = [ln.strip() for ln in sanitized_text.splitlines() if ln.strip()]
    candidate_name = "Candidat(e) Importé(e)"
    for ln in lines[:5]:
        if "CURRICULUM" not in ln.upper() and "MASQUÉ" not in ln.upper() and len(ln.split()) <= 4:
            candidate_name = ln
            break

    title_match = re.search(r"(?im)^Titre\s*:\s*(.+)$", sanitized_text)
    title = title_match.group(1).strip() if title_match else "Consultant(e) Data / IA"

    exp_match = re.search(r"(\d+)\s*ans?", sanitized_text, re.IGNORECASE)
    years_exp = int(exp_match.group(1)) if exp_match else 3

    tjm_match = re.search(r"(\d{3,4})\s*€", sanitized_text)
    tjm_eur = int(tjm_match.group(1)) if tjm_match else 520

    found_skills = [
        sk for sk in KNOWN_SKILLS
        if re.search(rf"\b{re.escape(sk)}\b", sanitized_text, re.IGNORECASE)
    ]
    if not found_skills:
        found_skills = ["Python", "APIs"]

    exp_lines = [ln.lstrip("-• ").strip() for ln in lines if ln.startswith(("-", "•"))][:4]

    profile = ConsultantProfile(
        id=f"CONS-IMP-{abs(hash(filename)) % 900 + 100}",
        pseudo_id=f"NEOSIA-IMP-{abs(hash(filename)) % 90 + 10}",
        full_name=candidate_name,
        title=title,
        years_exp=years_exp,
        skills=found_skills,
        tjm_eur=tjm_eur,
        availability="Immédiate" if "immédiate" in sanitized_text.lower() else "Sous 15j",
        location="Toulouse" if "toulouse" in sanitized_text.lower() else "France / Remote",
        summary=f"Profil extrait automatiquement ({years_exp} ans d'exp., {len(found_skills)} compétences clés).",
        experiences=exp_lines,
    )
    return profile, rgpd_event


def match_consultants_to_needs(
    consultants: List[ConsultantProfile], needs: List[ClientNeed]
) -> List[MatchResult]:
    """Calcule le score de matching multi-critères besoin <-> vivier."""
    results: List[MatchResult] = []
    for need in needs:
        req_lower = {s.lower(): s for s in need.required_skills}
        for c in consultants:
            c_lower = {s.lower() for s in c.skills}
            matched = [orig for low, orig in req_lower.items() if low in c_lower]
            missing = [orig for low, orig in req_lower.items() if low not in c_lower]

            skill_score = (len(matched) / max(len(need.required_skills), 1)) * 65
            exp_score = 15 if c.years_exp >= need.min_years_exp else 7
            tjm_ok = c.tjm_eur <= need.max_tjm_eur
            tjm_score = 10 if tjm_ok else 0
            avail_score = 10 if c.availability == "Immédiate" else (6 if c.availability == "Sous 15j" else 2)

            total_score = min(100, round(skill_score + exp_score + tjm_score + avail_score))
            rationale = (
                f"{len(matched)}/{len(need.required_skills)} compétences alignées, "
                f"{c.years_exp} ans d'exp. (min {need.min_years_exp}), "
                f"TJM {c.tjm_eur}€/{'OK' if tjm_ok else 'au-dessus du budget'}, "
                f"dispo {c.availability}."
            )
            results.append(
                MatchResult(
                    need_id=need.id,
                    need_title=need.title,
                    client_name=need.client_name,
                    consultant_id=c.id,
                    consultant_name=c.full_name,
                    score=total_score,
                    matched_skills=matched,
                    missing_skills=missing,
                    tjm_ok=tjm_ok,
                    rationale=rationale,
                )
            )
    results.sort(key=lambda r: r.score, reverse=True)
    return results


def generate_dossier_competences(
    consultant: ConsultantProfile, need: ClientNeed
) -> DossierCompetences:
    """Génère un Dossier de Compétences formaté NEOSIA prêt à envoyer."""
    skills_badges = " · ".join(f"`{s}`" for s in consultant.skills)
    exp_md = "\n".join(f"- {e}" for e in (consultant.experiences or [consultant.summary]))

    markdown = f"""# DOSSIER DE COMPÉTENCES — NEOSIA
**La performance autrement**

---

## Profil proposé : {consultant.full_name} (`{consultant.pseudo_id}`)
- **Intitulé :** {consultant.title}
- **Expérience :** {consultant.years_exp} ans
- **Localisation :** {consultant.location}
- **Disponibilité :** {consultant.availability} | **TJM :** {consultant.tjm_eur} € HT/jour
- **Besoin ciblé :** {need.title} (*{need.client_name}*)

---

## Synthèse de valeur pour {need.client_name}
{consultant.summary}

### Compétences clés validées
{skills_badges}

---

## Expériences significatives
{exp_md}

---
*Document généré automatiquement par la chaîne IA NEOSIA (conforme RGPD — données personnelles de contact filtrées).*
"""
    return DossierCompetences(
        consultant_id=consultant.id,
        consultant_name=consultant.full_name,
        target_need=f"{need.client_name} — {need.title}",
        markdown=markdown,
    )


def generate_prospection_campaign(
    need: ClientNeed, match: MatchResult
) -> ProspectionCampaign:
    """Génère un email + message LinkedIn ultra-personnalisés (Gemini si dispo, sinon déterministe)."""
    top_skills = ", ".join(match.matched_skills[:4]) or "Data & IA"
    subject = f"[{need.client_name}] Profil {match.consultant_name} disponible ({match.score}% match) — {need.title}"

    gemini_prompt = (
        f"Rédige en français un court email de prospection B2B (max 110 mots) de la part de NEOSIA "
        f"(vision : 'la performance autrement') adressé à {need.contact_name} ({need.contact_role} chez {need.client_name}). "
        f"Objet du besoin : {need.title}. Profil proposé : {match.consultant_name} (score {match.score}%, "
        f"compétences clés : {top_skills}). Ton direct, pragmatique, orienté ROI. Pas de blabla."
    )
    ai_body = _call_gemini_text(gemini_prompt)

    email_body = ai_body or (
        f"Bonjour {need.contact_name},\n\n"
        f"Suite à votre besoin « {need.title} » chez {need.client_name}, j'ai immédiatement rapproché notre vivier "
        f"et identifié un profil disponible qui correspond à {match.score}% à vos critères ({top_skills}).\n\n"
        f"• Consultant(e) : {match.consultant_name}\n"
        f"• Points forts : {match.rationale}\n\n"
        f"Je vous joins son Dossier de Compétences NEOSIA anonymisé et reste disponible pour un échange rapide de 15 min cette semaine.\n\n"
        f"Bien cordialement,\nL'équipe NEOSIA — Toulouse"
    )

    linkedin_dm = (
        f"Bonjour {need.contact_name}, j'ai vu votre recherche sur « {need.title} ». "
        f"Nous avons chez NEOSIA un profil {top_skills} disponible rapidement (match {match.score}%). "
        f"Puis-je vous transmettre son dossier de compétences ?"
    )

    return ProspectionCampaign(
        need_id=need.id,
        client_name=need.client_name,
        contact_name=need.contact_name,
        subject=subject,
        email_body=email_body,
        linkedin_dm=linkedin_dm,
    )
