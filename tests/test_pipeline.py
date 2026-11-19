from fastapi.testclient import TestClient
from app.main import app
from app.rgpd import sanitize_cv_for_llm

client = TestClient(app)


def test_rgpd_masks_pii_before_llm():
    raw = "Contact: jean.dupont@neosia.group | Tel: 06 12 34 56 78 | NIR: 1 90 05 31 555 123 45"
    sanitized, event = sanitize_cv_for_llm(raw, "test_cv.txt")
    assert "jean.dupont@neosia.group" not in sanitized
    assert "06 12 34 56 78" not in sanitized
    assert "[EMAIL_MASQUÉ_RGPD]" in sanitized
    assert "[TÉL_MASQUÉ_RGPD]" in sanitized
    assert event.entities_redacted >= 2


def test_health_endpoint():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "BoondManager API" in data["connectors"]


def test_e2e_pipeline_execution():
    resp = client.post("/api/run-e2e")
    assert resp.status_code == 200
    data = resp.json()
    assert data["kpis"]["cvs_processed"] >= 4
    assert len(data["matches"]) > 0
    assert data["sample_dossier"] is not None
    assert data["sample_campaign"] is not None


def test_n8n_webhook_and_pair_generation_and_reset():
    resp = client.post(
        "/api/webhooks/n8n",
        json={
            "event": "new_client_need",
            "client_name": "Toulouse Mobility",
            "title": "Architecte IA & n8n",
            "required_skills": ["Python", "n8n", "LLM"],
            "max_tjm_eur": 600,
            "contact_name": "Sophie Martin",
        },
    )
    assert resp.status_code == 200
    need_id = resp.json()["need"]["id"]

    d_resp = client.post("/api/dossier", json={"consultant_id": "CONS-001", "need_id": need_id})
    assert d_resp.status_code == 200
    assert "DOSSIER DE COMPÉTENCES" in d_resp.json()["markdown"]

    p_resp = client.post("/api/prospection", json={"consultant_id": "CONS-001", "need_id": need_id})
    assert p_resp.status_code == 200
    assert "Toulouse Mobility" in p_resp.json()["subject"]

    r_resp = client.post("/api/reset")
    assert r_resp.status_code == 200
    assert r_resp.json()["status"] == "reset_ok"
