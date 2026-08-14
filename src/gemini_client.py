"""
Google Gemini integration for InfraPulse.
Requires GOOGLE_API_KEY environment variable.
Falls back to rule-based logic if no key is present (for offline demo).
"""

import os
import json
import re
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

try:
    import google.generativeai as genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from prompts.system_prompts import (
    REQUEST_EXTRACTION_PROMPT,
    PRIORITIZATION_PROMPT,
    HOTSPOT_SUMMARY_PROMPT,
)


class GeminiClient:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        self.model = None
        self.use_ai = False

        if GENAI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(
                    model_name,
                    generation_config={
                        "temperature": 0.2,
                        "top_p": 0.9,
                        "max_output_tokens": 1024,
                        "response_mime_type": "application/json",
                    },
                )
                self.use_ai = True
            except Exception as e:
                print(f"[InfraPulse] Gemini init failed: {e}. Using rule-based fallback.")
        else:
            print("[InfraPulse] No GOOGLE_API_KEY found or library missing. Using rule-based fallback.")

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """Robustly extract JSON from model response."""
        text = text.strip()
        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        # Find first { ... }
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                pass
        return {}

    def extract_request(self, raw_text: str) -> Dict[str, Any]:
        """Structure a free-text citizen request."""
        if self.use_ai and self.model:
            try:
                prompt = f"{REQUEST_EXTRACTION_PROMPT}\n\nCitizen request:\n\"\"\"\n{raw_text}\n\"\"\""
                response = self.model.generate_content(prompt)
                data = self._extract_json(response.text)
                if data:
                    return data
            except Exception as e:
                print(f"[Gemini] extract_request error: {e}")

        # Fallback rule-based
        return self._fallback_extract(raw_text)

    def prioritize(
        self,
        district: str,
        state: str,
        demand_summary: str,
        demographics: Dict,
        infra: Dict,
        schemes: list,
    ) -> Dict[str, Any]:
        """Generate priority recommendation for a district."""
        if self.use_ai and self.model:
            try:
                context = f"""
District: {district}, {state}
Citizen demand signals: {demand_summary}
Demographics: population={demographics.get('population')}, poverty_rate={demographics.get('poverty_rate')}%, 
rural_pct={demographics.get('rural_pct')}%, literacy={demographics.get('literacy_rate')}%
Infrastructure gaps: road_all_weather={infra.get('all_weather_road_pct')}%, 
piped_water={infra.get('piped_water_pct')}%, toilet={infra.get('toilet_coverage_pct')}%, 
infra_gap_score={infra.get('infra_gap_score')} (higher = worse)
Relevant schemes: {schemes}
"""
                prompt = f"{PRIORITIZATION_PROMPT}\n\nContext:\n{context}"
                response = self.model.generate_content(prompt)
                data = self._extract_json(response.text)
                if data:
                    return data
            except Exception as e:
                print(f"[Gemini] prioritize error: {e}")

        return self._fallback_prioritize(district, state, demand_summary, demographics, infra)

    def generate_hotspot_briefing(self, hotspot_data: list) -> Dict[str, Any]:
        if self.use_ai and self.model:
            try:
                prompt = f"{HOTSPOT_SUMMARY_PROMPT}\n\nHotspot data:\n{json.dumps(hotspot_data, indent=2)}"
                response = self.model.generate_content(prompt)
                data = self._extract_json(response.text)
                if data:
                    return data
            except Exception as e:
                print(f"[Gemini] hotspot briefing error: {e}")

        return self._fallback_briefing(hotspot_data)

    # ---------- Rule-based fallbacks (always available) ----------

    def _fallback_extract(self, text: str) -> Dict[str, Any]:
        text_l = text.lower()
        category = "Other"
        if any(w in text_l for w in ["road", "bridge", "highway", "nh-", "path"]):
            category = "Road"
        elif any(w in text_l for w in ["water", "drinking", "pipeline", "hand pump", "irrigation", "arsenic", "fluoride"]):
            category = "Water"
        elif any(w in text_l for w in ["school", "classroom", "teacher", "education", "student"]):
            category = "Education"
        elif any(w in text_l for w in ["hospital", "phc", "doctor", "health", "ambulance", "medicine", "pregnant"]):
            category = "Health"
        elif any(w in text_l for w in ["power", "electricity", "solar", "outage", "cut"]):
            category = "Energy"
        elif any(w in text_l for w in ["toilet", "sanitation", "sewage", "garbage", "swachh"]):
            category = "Sanitation"
        elif any(w in text_l for w in ["flood", "embankment", "breach"]):
            category = "Flood Protection"

        urgency = "Medium"
        if any(w in text_l for w in ["urgent", "urgently", "dying", "collapsed", "completely broken", "no water", "cannot pass"]):
            urgency = "High"

        scheme_map = {
            "Road": "PM Gati Shakti / PMGSY",
            "Water": "Jal Jeevan Mission",
            "Education": "Samagra Shiksha",
            "Health": "Ayushman Bharat Health Infrastructure",
            "Energy": "Saubhagya / PM Surya Ghar",
            "Sanitation": "Swachh Bharat Mission 2.0",
            "Flood Protection": "Flood Management Programme",
        }

        return {
            "category": category,
            "urgency": urgency,
            "location_hint": None,
            "key_issues": [text[:80] + "..." if len(text) > 80 else text],
            "affected_population_estimate": "medium",
            "sentiment": "Frustrated" if urgency == "High" else "Neutral",
            "summary": text[:120] + ("..." if len(text) > 120 else ""),
            "suggested_scheme": scheme_map.get(category, "Relevant national scheme"),
        }

    def _fallback_prioritize(self, district, state, demand_summary, demo, infra) -> Dict[str, Any]:
        gap = infra.get("infra_gap_score", 50)
        poverty = demo.get("poverty_rate", 25)
        score = gap * 0.5 + poverty * 0.4 + 10  # rough
        rank = 1 if score > 70 else (2 if score > 55 else 3)

        # Infer dominant category from demand_summary
        cat = "Water"
        if "Road" in demand_summary:
            cat = "Road"
        elif "Health" in demand_summary:
            cat = "Health"
        elif "Education" in demand_summary:
            cat = "Education"

        return {
            "priority_rank": rank,
            "recommended_project": f"Priority {cat} intervention in {district}",
            "category": cat,
            "rationale": (
                f"High citizen demand combined with elevated poverty rate ({poverty}%) "
                f"and infrastructure gap score of {gap}. This district shows clear need "
                f"for targeted public investment aligned with national missions."
            ),
            "estimated_impact": f"Approx. {int(demo.get('population', 100000) * 0.3):,} residents",
            "suggested_budget_band": "10-40 Cr INR",
            "aligned_schemes": ["Relevant Central Sector Scheme"],
            "risk_if_delayed": "Continued service gaps will deepen inter-district inequality and human development losses.",
            "confidence": "Medium (rule-based fallback)",
        }

    def _fallback_briefing(self, hotspot_data: list) -> Dict[str, Any]:
        top = hotspot_data[:3] if hotspot_data else []
        return {
            "executive_summary": (
                "Citizen demand is concentrated in aspirational and high-poverty districts, "
                "with Water, Road and Health emerging as the strongest signals. "
                "Alignment with existing national missions can accelerate delivery."
            ),
            "top_3_hotspots": [
                {
                    "district_state": f"{h.get('district')}, {h.get('state')}",
                    "primary_need": h.get("top_category", "Infrastructure"),
                    "demand_intensity": "High",
                    "why_urgent": h.get("reason", "High volume of citizen requests + infrastructure gaps"),
                }
                for h in top
            ],
            "cross_cutting_theme": "Water security and last-mile connectivity remain the binding constraints in most high-demand districts.",
            "policy_recommendation": "Ring-fence a share of Gati Shakti and Jal Jeevan Mission allocations for the top 20 demand hotspots identified by citizen signals.",
        }
