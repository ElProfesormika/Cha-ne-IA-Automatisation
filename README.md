# TalentFlow AI — Chaîne IA & Automatisation (De la détection du besoin au placement)

Prototype opérationnel de bout en bout d'automatisation du recrutement, du matching et de la prospection B2B pour cabinets de conseil / ESN.

## Ce que fait cette chaîne automatisée

1. **Sourcing & Tri des CV avec l'IA (RGPD-by-Design)** : extraction structurée de CV (`.pdf`, `.txt`, `.md`) avec masquage automatique des données personnelles (emails, téléphones, NIR) avant tout traitement LLM (`app/rgpd.py`).
2. **Suivi des besoins marché & Matching Vivier** : scoring multi-critères (compétences, séniorité, TJM, disponibilité) entre les besoins clients et le vivier de consultants (`app/pipeline.py`).
3. **Génération automatique des Dossiers de Compétences** : création instantanée d'un Dossier de Compétences formaté et téléchargeable en `.md`.
4. **Campagnes de prospection personnalisées** : rédaction d'emails B2B et messages LinkedIn ciblés (via **Gemini 2.5 Flash** si `GEMINI_API_KEY` est configurée, ou moteur déterministe).
5. **Connecteurs API & Agents** : hub d'intégration prêt pour **BoondManager**, **CRM**, **Microsoft 365** et webhooks **n8n / Make / Power Automate** (`POST /api/webhooks/n8n`).
6. **Tableau de bord hebdomadaire** : pilotage en temps réel des KPIs métier et du temps économisé (`static/index.html`).

## Lancer le projet en 30 secondes

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8010
```

Ouvrir `http://127.0.0.1:8010` dans votre navigateur.

## Lancer les tests unitaires (`pytest`)

```bash
.venv/bin/pytest -v
```
