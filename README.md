# InfraPulse  
**AI-powered Citizen Demand Aggregation & Infrastructure Prioritization Platform**  
*Digital Public Good prototype for BRICS nations — India (English) demo*

[![Python](https://img.shields.io/badge/Python-3.10+-blue)]()
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)]()
[![Google Gemini](https://img.shields.io/badge/Google%20AI-Gemini-4285F4)]()

## The Problem
Governments across BRICS struggle to consolidate citizen feedback and align it with national infrastructure priorities. Development requests live in fragmented systems → misaligned public spending, unaddressed gaps, and no clear way to measure impact of digital public infrastructure.

## The Solution
InfraPulse is a scalable, multilingual AI platform that:

1. Ingests citizen development requests via voice, text & messaging apps  
2. Uses **Google Gemini** to structure, classify and prioritise them  
3. Fuses requests with demographic data, infrastructure indices and public investment plans  
4. Surfaces **demand hotspots** and generates ranked project recommendations for national policymakers  

Designed from day one as a **Digital Public Good** that works across BRICS linguistic and administrative diversity.

## Quick Start

```bash
# 1. Clone / enter project
cd infrapulse

# 2. Create virtualenv (recommended)
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional but recommended) Add Google AI key
cp .env.example .env
# Edit .env and set GOOGLE_API_KEY=your_key_here
# Get a key at https://aistudio.google.com/app/apikey

# 5. Run the prototype
streamlit run app.py
```

Open http://localhost:8501

> Without an API key the app still runs fully using intelligent rule-based fallbacks so judges can evaluate the end-to-end flow immediately.

## Project Structure

```
infrapulse/
├── app.py                  # Streamlit end-to-end application
├── requirements.txt
├── .env.example
├── data/
│   ├── citizen_requests.csv
│   ├── demographics.csv
│   ├── infrastructure_indices.csv
│   └── investment_plans.csv
├── src/
│   ├── gemini_client.py    # Google Gemini integration + fallbacks
│   └── data_loader.py
├── prompts/
│   └── system_prompts.py   # Production-grade Gemini prompts
└── README.md
```

## Google AI Integration

| Capability | Model / Method | Purpose |
|------------|----------------|---------|
| Request understanding | Gemini 1.5 Flash | Free-text → structured JSON (category, urgency, issues, scheme) |
| Project prioritisation | Gemini 1.5 Flash | Multi-signal ranking + natural-language rationale |
| Executive briefing | Gemini 1.5 Flash | Hotspot synthesis for policymakers |
| Future | Speech-to-Text + Gemini | Native voice in 100+ languages |

All prompts are designed to be language-agnostic so the same pipeline works for Hindi, Portuguese, Russian, Mandarin, Arabic, etc.

## Sample Data (India)

- **30 realistic citizen requests** across 13 states / 25 districts (aspirational & high-poverty focus)
- Demographic indicators aligned with Census / NFHS patterns
- Infrastructure gap scores (roads, water, electricity, toilets, health facilities)
- National schemes: PM Gati Shakti, Jal Jeevan Mission, Samagra Shiksha, Ayushman Bharat, PMGSY, etc.

## Cross-border / Multilingual Design

- Core scoring logic is country-agnostic
- Scheme registry is a simple CSV that any BRICS member can replace
- Gemini handles translation + cultural context natively
- District-level unit of analysis maps cleanly to municipalities / oblasts / provinces elsewhere

## Demo Script (3–5 min)

1. **Citizen Portal** – submit a new request in natural language → show Gemini structuring it  
2. **Dashboard** – live metrics + category & geography charts  
3. **Hotspots** – interactive scatter of poverty × infra gap × demand; generate AI briefing  
4. **AI Recommendations** – pick a top district → Gemini produces ranked project + justification + budget band + risk  
5. **About** – architecture & DPG positioning

## Submission Package Checklist

- [x] Working end-to-end prototype (this repo)
- [x] Mandatory Google AI integration (Gemini)
- [x] Realistic sample data
- [x] Cross-border design
- [x] Multilingual-ready architecture (English demo)
- [ ] Pitch deck (separate .pptx)
- [ ] 3–5 min demo video
- [ ] Deployed link (Streamlit Community Cloud / Hugging Face / Cloud Run)
- [ ] 2–3 line description

## Licence
Intended as a Digital Public Good. Open-source release under a permissive licence suitable for government adoption (to be finalised).

---
Built for the BRICS Digital Public Goods Challenge • India English prototype
