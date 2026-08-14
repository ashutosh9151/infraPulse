"""
InfraPulse – AI-powered Citizen Demand Aggregation & Infrastructure Prioritization
Digital Public Good prototype for BRICS nations (India demo)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import sys

# Ensure src is importable
sys.path.insert(0, os.path.dirname(__file__))

from src.data_loader import DataStore
from src.gemini_client import GeminiClient

# ---------- Page config ----------
st.set_page_config(
    page_title="InfraPulse | BRICS Digital Public Good",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.4rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.1rem;
        color: #475569;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #0f766e 0%, #0d9488 100%);
        padding: 1.2rem;
        border-radius: 12px;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Init ----------
@st.cache_resource
def get_store():
    return DataStore()

@st.cache_resource
def get_gemini():
    return GeminiClient()

store = get_store()
gemini = get_gemini()

# ---------- Sidebar ----------
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/satellite.png", width=64)
    st.title("InfraPulse")
    st.caption("Digital Public Good • BRICS")
    st.markdown("---")
    st.markdown("**Demo focus:** India (English)")
    st.markdown("**Designed for:** All BRICS nations")
    st.markdown("---")
    st.info(
        "Set `GOOGLE_API_KEY` in environment or `.env` for full Gemini power. "
        "Without it, rule-based fallbacks keep the demo fully functional."
    )
    if gemini.use_ai:
        st.success("✅ Google Gemini connected")
    else:
        st.warning("⚠️ Gemini offline – using intelligent fallbacks")

# ---------- Header ----------
st.markdown('<p class="main-header">🛰️ InfraPulse</p>', unsafe_allow_html=True)
st.markdown(
    '<p class="sub-header">AI platform that turns citizen development requests into prioritised national infrastructure investments</p>',
    unsafe_allow_html=True,
)

# ---------- Tabs ----------
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📥 Citizen Portal",
    "📊 Policymaker Dashboard",
    "🔥 Demand Hotspots",
    "🤖 AI Recommendations",
    "ℹ️ About & Architecture",
])

# ==================== TAB 1: Citizen Portal ====================
with tab1:
    st.subheader("Submit a Development Request")
    st.caption("In production this connects to WhatsApp, Telegram, IVR voice, and web forms in any language.")

    col1, col2 = st.columns([2, 1])

    with col1:
        with st.form("citizen_form"):
            state = st.selectbox(
                "State",
                sorted(store.requests["state"].unique().tolist()),
            )
            district = st.selectbox(
                "District",
                sorted(store.requests[store.requests["state"] == state]["district"].unique().tolist())
                if state else [],
            )
            raw_text = st.text_area(
                "Describe the infrastructure need (voice transcription would appear here)",
                height=140,
                placeholder="Example: The road from our village to the block headquarters is completely damaged after the rains. School children and patients cannot travel safely...",
            )
            source = st.selectbox("Channel", ["WhatsApp", "Web", "Telegram", "Voice (IVR)", "Other"])
            submitted = st.form_submit_button("Submit Request", type="primary", use_container_width=True)

        if submitted and raw_text.strip():
            with st.spinner("AI is analysing your request..."):
                extracted = gemini.extract_request(raw_text)

            st.success("Request received and structured by AI")
            st.json(extracted)

            # Persist in session for demo
            new_id = f"REQ{len(store.requests) + 1:03d}"
            new_row = {
                "request_id": new_id,
                "timestamp": datetime.now().isoformat(),
                "state": state,
                "district": district,
                "category": extracted.get("category", "Other"),
                "raw_text": raw_text,
                "urgency": extracted.get("urgency", "Medium"),
                "source": source,
                "lat": 20.0,  # placeholder
                "lon": 78.0,
                "language": "en",
            }
            store.add_request(new_row)
            st.balloons()

    with col2:
        st.markdown("### How it works")
        st.markdown("""
        1. Citizen speaks or types in any language  
        2. **Google Gemini** extracts category, urgency, location, key issues  
        3. Request joins the national demand dataset  
        4. Policymakers see updated hotspots in near real-time  
        """)
        st.markdown("### Supported channels (production)")
        st.markdown("- WhatsApp Business API  \n- Telegram Bot  \n- IVR / Voice  \n- Web & Mobile forms  \n- CSC / Common Service Centres")

# ==================== TAB 2: Policymaker Dashboard ====================
with tab2:
    st.subheader("National Demand Overview – India")

    stats = store.get_district_stats()
    total_req = len(store.requests)
    high_urg = (store.requests["urgency"] == "High").sum()
    districts_covered = store.requests[["state", "district"]].drop_duplicates().shape[0]
    states_covered = store.requests["state"].nunique()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Citizen Requests", f"{total_req:,}")
    m2.metric("High Urgency", f"{high_urg:,}", delta=f"{high_urg/total_req*100:.0f}%")
    m3.metric("Districts Covered", districts_covered)
    m4.metric("States", states_covered)

    st.markdown("---")

    c1, c2 = st.columns(2)

    with c1:
        cat_counts = store.requests["category"].value_counts().reset_index()
        cat_counts.columns = ["Category", "Count"]
        fig = px.bar(
            cat_counts,
            x="Category",
            y="Count",
            color="Count",
            color_continuous_scale="Teal",
            title="Demand by Infrastructure Category",
        )
        fig.update_layout(showlegend=False, height=360)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        state_counts = store.requests["state"].value_counts().reset_index()
        state_counts.columns = ["State", "Count"]
        fig2 = px.pie(
            state_counts,
            names="State",
            values="Count",
            title="Geographic Distribution of Requests",
            hole=0.45,
        )
        fig2.update_layout(height=360)
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("### Latest Requests")
    st.dataframe(
        store.requests.sort_values("timestamp", ascending=False)[
            ["request_id", "timestamp", "state", "district", "category", "urgency", "raw_text"]
        ].head(12),
        use_container_width=True,
        hide_index=True,
    )

# ==================== TAB 3: Demand Hotspots ====================
with tab3:
    st.subheader("🔥 Demand Hotspots – Where Citizen Voice + Data Meet")
    st.caption("Scored by: request volume × urgency × infrastructure gap × poverty rate")

    hotspots = store.get_hotspots(10)

    # Table
    display_cols = [
        "state", "district", "total_requests", "high_urgency_count",
        "top_category", "poverty_rate", "infra_gap_score", "demand_score",
    ]
    st.dataframe(
        hotspots[display_cols].round(1),
        use_container_width=True,
        hide_index=True,
    )

    # Scatter: poverty vs infra gap, size = demand
    fig3 = px.scatter(
        hotspots,
        x="poverty_rate",
        y="infra_gap_score",
        size="total_requests",
        color="top_category",
        hover_name="district",
        hover_data=["state", "demand_score"],
        title="Hotspot Map: Poverty × Infrastructure Gap (bubble size = citizen demand)",
        labels={
            "poverty_rate": "Poverty Rate (%)",
            "infra_gap_score": "Infrastructure Gap Score (higher = worse)",
        },
        height=480,
    )
    st.plotly_chart(fig3, use_container_width=True)

    # AI Briefing
    st.markdown("### 🤖 AI-Generated Executive Briefing")
    if st.button("Generate Policymaker Briefing with Gemini"):
        with st.spinner("Gemini is synthesising the national picture..."):
            hs_list = hotspots.head(5)[
                ["state", "district", "top_category", "total_requests", "demand_score", "poverty_rate"]
            ].to_dict(orient="records")
            briefing = gemini.generate_hotspot_briefing(hs_list)

        st.markdown(f"**Executive Summary**  \n{briefing.get('executive_summary', '')}")
        st.markdown("**Top Hotspots**")
        for h in briefing.get("top_3_hotspots", []):
            st.markdown(
                f"- **{h.get('district_state')}** – {h.get('primary_need')} "
                f"({h.get('demand_intensity')}): {h.get('why_urgent')}"
            )
        st.markdown(f"**Cross-cutting theme:** {briefing.get('cross_cutting_theme', '')}")
        st.success(f"**Policy recommendation:** {briefing.get('policy_recommendation', '')}")

# ==================== TAB 4: AI Recommendations ====================
with tab4:
    st.subheader("🎯 High-Priority Project Recommendations")
    st.caption("Gemini combines citizen demand + demographics + infrastructure indices + national schemes")

    hotspots = store.get_hotspots(8)
    selected = st.selectbox(
        "Select a hotspot district for detailed recommendation",
        options=hotspots.apply(lambda r: f"{r['district']}, {r['state']}", axis=1).tolist(),
    )

    if selected:
        dist, state = selected.split(", ")
        row = hotspots[(hotspots["district"] == dist) & (hotspots["state"] == state)].iloc[0]

        demand_summary = (
            f"{int(row['total_requests'])} requests, "
            f"{int(row['high_urgency_count'])} high-urgency, "
            f"dominant category: {row['top_category']}"
        )
        demo = {
            "population": row.get("population"),
            "poverty_rate": row.get("poverty_rate"),
            "rural_pct": row.get("rural_pct"),
            "literacy_rate": row.get("literacy_rate"),
        }
        infra = {
            "all_weather_road_pct": row.get("all_weather_road_pct"),
            "piped_water_pct": row.get("piped_water_pct"),
            "toilet_coverage_pct": row.get("toilet_coverage_pct"),
            "infra_gap_score": row.get("infra_gap_score"),
        }
        schemes = store.get_schemes_for_category(row["top_category"])

        if st.button("Generate AI Priority Recommendation", type="primary"):
            with st.spinner("Google Gemini is ranking and justifying the intervention..."):
                rec = gemini.prioritize(dist, state, demand_summary, demo, infra, schemes)

            st.markdown("---")
            col_a, col_b = st.columns([1, 2])
            with col_a:
                st.metric("Priority Rank", f"#{rec.get('priority_rank', '–')}")
                st.metric("Confidence", rec.get("confidence", "–"))
                st.metric("Budget Band", rec.get("suggested_budget_band", "–"))
            with col_b:
                st.markdown(f"### {rec.get('recommended_project', 'Recommended Project')}")
                st.markdown(f"**Category:** {rec.get('category')}")
                st.markdown(f"**Estimated Impact:** {rec.get('estimated_impact')}")
                st.markdown(f"**Aligned Schemes:** {', '.join(rec.get('aligned_schemes', []))}")

            st.markdown("#### Rationale")
            st.write(rec.get("rationale", ""))
            st.warning(f"**Risk if delayed:** {rec.get('risk_if_delayed', '')}")

# ==================== TAB 5: About ====================
with tab5:
    st.subheader("About InfraPulse")
    st.markdown("""
**InfraPulse** is a scalable, multilingual AI platform designed as a **Digital Public Good** 
for BRICS nations. It aggregates citizen development requests arriving via voice, text and 
messaging apps, fuses them with demographic data, infrastructure indices and public investment 
plans, then surfaces demand hotspots and ranked project recommendations for national policymakers.

### Core Value
- Closes the feedback loop between citizens and large-scale infrastructure spending
- Makes public investment more demand-responsive and equitable
- Works across linguistic and administrative diversity of BRICS countries

### Technology Stack
| Layer | Choice |
|-------|--------|
| AI | **Google Gemini** (extraction, prioritisation, briefing) |
| Frontend | Streamlit (rapid, accessible demo) |
| Data | Public + realistic sample datasets (Census-style, scheme data) |
| Future | WhatsApp Business, Telegram, Google Speech-to-Text, geospatial layers |

### Cross-border design
- Language-agnostic core (Gemini native multilingual)
- Configurable national scheme registry
- District / municipality level scoring that maps to any federal structure
- Open data contracts so other countries can plug in their own demographic & budget data

### Sample Data Sources (India demo)
- Synthetic but realistic citizen requests modelled on real aspirational districts
- Demographic indicators aligned with Census / NFHS patterns
- Infrastructure indices reflecting known gaps (road density, piped water, electricity, toilets)
- National schemes: PM Gati Shakti, Jal Jeevan Mission, Samagra Shiksha, Ayushman Bharat, etc.

### Google AI Integration Points
1. **Request understanding** – free text → structured JSON (category, urgency, issues)
2. **Prioritisation engine** – multi-signal ranking + natural language justification
3. **Executive briefing** – automatic synthesis for cabinet / planning commission level

### Next steps for production
- Live WhatsApp & IVR connectors
- Full geospatial (PostGIS + satellite indices)
- Differential privacy & consent layer
- Open-source release under DPG licence
- Country adapters for Brazil, South Africa, Indonesia, UAE, etc.
    """)

    st.markdown("---")
    st.markdown("**Built for the BRICS Digital Public Goods Challenge** • India English prototype • Ready for multilingual expansion")
