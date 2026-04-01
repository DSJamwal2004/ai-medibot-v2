"""
Seed script — populates the medical_documents table with demo data.
Run once after docker-compose up:

  docker-compose exec backend python -m app.scripts.seed_documents
"""
from __future__ import annotations

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

MEDICAL_DOCUMENTS = [
    {
        "title": "Chest Pain — Emergency Assessment",
        "content": (
            "Chest pain is a common emergency presentation that requires immediate assessment. "
            "Causes range from life-threatening (myocardial infarction, pulmonary embolism, aortic dissection) "
            "to benign (musculoskeletal, gastroesophageal reflux). "
            "Red flags include: radiation to arm or jaw, diaphoresis, dyspnea, nausea. "
            "Any patient presenting with chest pain should have ECG within 10 minutes."
        ),
        "source": "Clinical Emergency Guidelines",
        "medical_domain": "cardiology",
        "authority_level": 3,
    },
    {
        "title": "Fever — Assessment and Management",
        "content": (
            "Fever is defined as a temperature >38°C (100.4°F). Common causes include viral infections, "
            "bacterial infections, and inflammatory conditions. "
            "Management: antipyretics (paracetamol 500-1000mg every 4-6 hours, max 4g/day), "
            "adequate hydration, rest. "
            "Seek urgent care if fever >39.5°C, fever with stiff neck (meningitis), "
            "fever lasting more than 3 days, or fever with rash."
        ),
        "source": "WHO Primary Care Guidelines",
        "medical_domain": "general",
        "authority_level": 3,
    },
    {
        "title": "Headache — Types and Red Flags",
        "content": (
            "Headaches are classified as primary (tension, migraine, cluster) or secondary. "
            "Tension headache: bilateral, pressing quality, not worsened by activity. "
            "Migraine: unilateral, pulsating, moderate-severe, often with nausea/photophobia, lasts 4-72 hours. "
            "Red flags (SNOOP): Systemic symptoms, Neurological symptoms, Onset sudden/thunderclap, "
            "Older age (>50), Previous headache history changed. "
            "Thunderclap headache (worst headache of life) requires immediate CT scan to rule out subarachnoid hemorrhage."
        ),
        "source": "NIH Neurology Guidelines",
        "medical_domain": "neurology",
        "authority_level": 3,
    },
    {
        "title": "Stroke — FAST Recognition and Response",
        "content": (
            "FAST acronym for stroke recognition: Face drooping (ask to smile), "
            "Arm weakness (ask to raise both arms), Speech difficulty (ask to repeat a phrase), "
            "Time to call emergency services immediately. "
            "Additional symptoms: sudden vision changes, severe headache without cause, "
            "sudden trouble walking or loss of balance. "
            "Treatment window: IV thrombolysis within 4.5 hours, thrombectomy within 24 hours. "
            "Note time of symptom onset. Do NOT give aspirin before CT scan."
        ),
        "source": "WHO Stroke Guidelines",
        "medical_domain": "neurology",
        "authority_level": 3,
    },
    {
        "title": "Diabetes — Type 2 Management",
        "content": (
            "Type 2 diabetes is characterised by insulin resistance and relative insulin deficiency. "
            "Symptoms: polyuria, polydipsia, blurred vision, fatigue, recurrent infections. "
            "Diagnosis: fasting glucose ≥7.0 mmol/L, HbA1c ≥48 mmol/mol. "
            "First-line treatment: lifestyle modification + metformin. "
            "Monitoring: HbA1c every 3-6 months, annual eye exam, foot exam, kidney function. "
            "Hypoglycaemia (glucose <4 mmol/L): treat with 15g fast-acting carbohydrate."
        ),
        "source": "WHO Diabetes Guidelines",
        "medical_domain": "endocrinology",
        "authority_level": 3,
    },
    {
        "title": "Asthma — Symptoms and Management",
        "content": (
            "Asthma is a chronic inflammatory airway disease. "
            "Symptoms: recurrent wheeze, breathlessness, chest tightness, cough (especially at night). "
            "Triggers: allergens, exercise, cold air, respiratory infections, NSAIDs. "
            "Acute attack: short-acting beta2-agonist (salbutamol) inhaler as reliever. "
            "Severe attack (cannot speak in sentences, RR >25, SpO2 <92%): call emergency services. "
            "Preventer inhalers: inhaled corticosteroids reduce frequency of attacks."
        ),
        "source": "WHO Respiratory Guidelines",
        "medical_domain": "respiratory",
        "authority_level": 3,
    },
    {
        "title": "Ibuprofen — Drug Information",
        "content": (
            "Ibuprofen is an NSAID used for pain, fever, and inflammation. "
            "Adult dose: 200-400mg every 4-6 hours, max 1200mg/day OTC (2400mg with doctor supervision). "
            "Take with food to reduce GI side effects. "
            "Contraindications: peptic ulcer, severe renal/hepatic impairment, heart failure. "
            "Interactions: increases bleeding risk with warfarin; reduces antihypertensive effect of ACE inhibitors. "
            "Avoid in pregnancy (especially 3rd trimester) and in patients with aspirin-sensitive asthma."
        ),
        "source": "NHS Drug Formulary",
        "medical_domain": "pharmacology",
        "authority_level": 2,
    },
    {
        "title": "Paracetamol (Acetaminophen) — Drug Information",
        "content": (
            "Paracetamol is an analgesic and antipyretic. "
            "Adult dose: 500-1000mg every 4-6 hours, max 4g/day (2g/day in liver disease or alcohol use). "
            "Overdose is a medical emergency — causes severe liver damage. "
            "Treatment for overdose: N-acetylcysteine (NAC) — most effective if given within 8 hours. "
            "Safe in pregnancy and breastfeeding at standard doses. "
            "Can be combined with ibuprofen for enhanced pain relief — take at alternating intervals."
        ),
        "source": "NHS Drug Formulary",
        "medical_domain": "pharmacology",
        "authority_level": 2,
    },
    {
        "title": "Hypertension — Blood Pressure Management",
        "content": (
            "Hypertension (high blood pressure) is defined as systolic ≥140 mmHg or diastolic ≥90 mmHg. "
            "Stage 1: 140-159/90-99. Stage 2: 160+/100+. Hypertensive crisis: >180/120 with organ damage. "
            "Lifestyle modifications: reduce sodium, increase physical activity, lose weight, limit alcohol. "
            "First-line medications: ACE inhibitors, ARBs, calcium channel blockers, thiazide diuretics. "
            "Hypertensive emergency: severe headache, vision changes, chest pain — requires immediate care."
        ),
        "source": "WHO Cardiovascular Guidelines",
        "medical_domain": "cardiology",
        "authority_level": 3,
    },
    {
        "title": "COVID-19 — Symptoms and When to Seek Care",
        "content": (
            "COVID-19 symptoms: fever, cough, fatigue, loss of taste/smell, headache, sore throat, "
            "shortness of breath, muscle aches, diarrhoea, runny nose. "
            "Severity range from mild (home isolation) to severe (hospitalisation). "
            "Seek emergency care if: severe shortness of breath, persistent chest pain, "
            "confusion, inability to stay awake, bluish lips. "
            "Home management: rest, fluids, paracetamol for fever. "
            "Isolation: follow current local health authority guidelines."
        ),
        "source": "WHO COVID-19 Guidelines",
        "medical_domain": "infectious_disease",
        "authority_level": 3,
    },
]


def seed():
    from app.db.session import SessionLocal
    from app.models import MedicalDocument
    from app.services.embeddings import embed

    db = SessionLocal()
    try:
        existing = db.query(MedicalDocument).count()
        if existing > 0:
            print(f"✅ Already have {existing} documents. Skipping seed.")
            return

        print(f"🌱 Seeding {len(MEDICAL_DOCUMENTS)} medical documents...")
        for i, doc_data in enumerate(MEDICAL_DOCUMENTS):
            print(f"  [{i+1}/{len(MEDICAL_DOCUMENTS)}] Embedding: {doc_data['title']}")
            embedding = embed(doc_data["title"] + " " + doc_data["content"])

            doc = MedicalDocument(
                title=doc_data["title"],
                content=doc_data["content"],
                source=doc_data["source"],
                medical_domain=doc_data["medical_domain"],
                authority_level=doc_data["authority_level"],
                chunk_index=0,
                embedding=embedding,
            )
            db.add(doc)

        db.commit()
        print(f"✅ Seeded {len(MEDICAL_DOCUMENTS)} documents successfully.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
