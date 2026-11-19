from typing import List
from app.models import ClientNeed, ConsultantProfile

SAMPLE_CV_TEXT = """
CURRICULUM VITAE
Camille Lefèvre
Email : camille.lefevre@exemple-mail.fr | Tél : +33 6 42 88 19 04
Localisation : Toulouse (31) — Télétravail hybride OK
Titre : Ingénieure Data & IA Senior (6 ans d'expérience)
TJM indicatif : 560 € / jour | Disponibilité : Immédiate

COMPÉTENCES CLÉS
Python, FastAPI, LangChain, Gemini API, Vertex AI, SQL, PostgreSQL, Docker, n8n, Power Automate, Azure, RGPD

EXPÉRIENCES RÉCENTES
- Lead Data & IA chez AeroData Toulouse (2023 - 2026) : Déploiement de pipelines RAG et automatisation de tri documentaire via Python, FastAPI et Vertex AI (-65% de temps de traitement).
- Data Engineer chez Occitanie Tech (2020 - 2023) : Orchestration ETL, APIs REST et connecteurs CRM/ERP (HubSpot, Microsoft 365).
"""


def get_initial_consultants() -> List[ConsultantProfile]:
    return [
        ConsultantProfile(
            id="CONS-001",
            pseudo_id="TF-C01",
            full_name="Lucas Moreau",
            title="Architecte Cloud & IA Générative",
            years_exp=7,
            skills=["Python", "FastAPI", "LLM", "Gemini", "GCP", "Docker", "Kubernetes", "RGPD"],
            tjm_eur=620,
            availability="Immédiate",
            location="Toulouse",
            summary="7 ans d'expérience en architecture Cloud GCP et déploiement d'agents IA sécurisés en production.",
            experiences=[
                "Airbus Digital (2023-2026) : Industrialisation de pipelines LLM & RAG sur Google Cloud Run.",
                "Capgemini Toulouse (2020-2023) : APIs Python/FastAPI et gouvernance données RGPD.",
            ],
        ),
        ConsultantProfile(
            id="CONS-002",
            pseudo_id="TF-C02",
            full_name="Sarah Benali",
            title="Consultante Automatisation & Data",
            years_exp=4,
            skills=["Python", "n8n", "Make", "Power Automate", "Microsoft 365", "CRM", "APIs", "SQL"],
            tjm_eur=490,
            availability="Immédiate",
            location="Toulouse / Remote",
            summary="Spécialiste automatisation no-code/low-code (n8n, Make, Power Automate) et intégration CRM/M365.",
            experiences=[
                "Pierre Fabre (2024-2026) : Automatisation des workflows RH et CRM avec n8n, Power Automate et Graph API.",
                "ScaleUp Occitanie (2022-2024) : Connecteurs Python entre BoondManager, HubSpot et Teams.",
            ],
        ),
        ConsultantProfile(
            id="CONS-003",
            pseudo_id="TF-C03",
            full_name="Thomas Girard",
            title="Data Engineer & MLOps",
            years_exp=5,
            skills=["Python", "SQL", "Airflow", "dbt", "Azure", "FastAPI", "Docker"],
            tjm_eur=540,
            availability="Sous 15j",
            location="Toulouse",
            summary="Ingénieur Data & MLOps orienté fiabilité des pipelines et tableaux de bord décisionnels.",
            experiences=[
                "Continental Automotive (2022-2026) : Pipelines temps réel Python/Airflow et dashboards KPI.",
                "Sopra Steria (2021-2022) : Modernisation Data Warehouse SQL/Azure.",
            ],
        ),
        ConsultantProfile(
            id="CONS-004",
            pseudo_id="TF-C04",
            full_name="Inès Laurent",
            title="Chef de Projet CRM & BoondManager",
            years_exp=6,
            skills=["BoondManager", "CRM", "Microsoft 365", "Power BI", "APIs", "RGPD"],
            tjm_eur=530,
            availability="En mission (fin 30j)",
            location="Toulouse",
            summary="Experte pilotage ESN, structuration BoondManager, reporting hebdomadaire et conformité RGPD.",
            experiences=[
                "ESN Sud-Ouest (2022-2026) : Refonte du processus avant-vente et KPIs hebdomadaires direction.",
            ],
        ),
    ]


def get_initial_needs() -> List[ClientNeed]:
    return [
        ClientNeed(
            id="NEED-101",
            client_name="AeroSpace Systems Toulouse",
            sector="Aéronautique",
            title="Ingénieur IA & Pipelines Documentaires (LLM / Python)",
            required_skills=["Python", "FastAPI", "LLM", "Docker", "RGPD"],
            min_years_exp=4,
            max_tjm_eur=650,
            location="Toulouse",
            urgency="Haute",
            contact_name="Claire Dupuis",
            contact_role="Directrice Data & Innovation",
            source="BoondManager",
        ),
        ClientNeed(
            id="NEED-102",
            client_name="BioSanté Occitanie",
            sector="Santé / Pharma",
            title="Consultant Automatisation Workflows (n8n / M365 / CRM)",
            required_skills=["n8n", "Power Automate", "Microsoft 365", "CRM", "APIs", "Python"],
            min_years_exp=3,
            max_tjm_eur=520,
            location="Toulouse / Remote",
            urgency="Haute",
            contact_name="Marc Valéry",
            contact_role="Responsable SI Métier",
            source="M365_Email",
        ),
        ClientNeed(
            id="NEED-103",
            client_name="FinTech Garonne",
            sector="Finance",
            title="Data Engineer MLOps & KPIs Temps Réel",
            required_skills=["Python", "SQL", "Docker", "FastAPI", "Azure"],
            min_years_exp=4,
            max_tjm_eur=580,
            location="Toulouse",
            urgency="Moyenne",
            contact_name="Julien Mercier",
            contact_role="VP Engineering",
            source="CRM",
        ),
    ]
