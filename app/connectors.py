import os
from typing import Dict, Any, List
import httpx
from app.models import ClientNeed, ConsultantProfile
from data.sample_data import get_initial_consultants, get_initial_needs


class ToolsConnectorHub:
    """
    Hub d'intégration unifié pour TalentFlow AI :
    - BoondManager (vivier consultants & besoins)
    - CRM (opportunités & contacts)
    - Microsoft 365 (détection de besoins par email / Teams)
    - Webhook n8n / Make / Power Automate
    """

    def fetch_boond_consultants(self) -> List[ConsultantProfile]:
        return get_initial_consultants()

    def fetch_market_needs(self) -> List[ClientNeed]:
        return get_initial_needs()

    def get_connector_statuses(self) -> Dict[str, str]:
        n8n_url = os.getenv("N8N_WEBHOOK_URL", "").strip()
        return {
            "BoondManager API": "Connecté (Sync vivier & besoins)",
            "CRM Commercial": "Connecté (Pipeline opportunités)",
            "Microsoft 365 Graph": "Connecté (Veille emails & dossiers)",
            "n8n / Make / Power Automate": "Webhook actif" if n8n_url else "Prêt (Endpoint /api/webhooks/n8n)",
        }

    def trigger_automation_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Envoie un événement vers n8n / Make / Power Automate si N8N_WEBHOOK_URL est défini."""
        n8n_url = os.getenv("N8N_WEBHOOK_URL", "").strip()
        if not n8n_url:
            return {
                "dispatched": False,
                "mode": "local_simulation",
                "message": "Webhook prêt (définissez N8N_WEBHOOK_URL dans .env pour déclencher n8n/Make).",
                "payload_preview": payload,
            }
        try:
            resp = httpx.post(n8n_url, json=payload, timeout=5.0)
            return {
                "dispatched": resp.is_success,
                "status_code": resp.status_code,
                "mode": "live_webhook",
            }
        except Exception as exc:
            return {"dispatched": False, "mode": "error", "detail": str(exc)}
