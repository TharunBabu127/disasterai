import streamlit as st
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import folium
from streamlit_folium import st_folium
from disaster_ai import assess_risk, DISASTER_TYPES, fetch_usgs_earthquakes, fetch_gdacs_disasters
# ---- PAGE CONFIG ----
st.set_page_config(
    page_title="DisasterAI — Command Center",
    page_icon="🚨",
    layout="wide"
)

# ---- CUSTOM STYLE ----
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #0a0e1a 0%, #0d1b2a 100%);
    }
    [data-testid="stSidebar"] {
        background: #0d1b2a;
        border-right: 1px solid #1e3a5f;
    }
    .header-box {
        background: linear-gradient(90deg, #1a1f3a, #0d2137);
        border: 1px solid #1e3a5f;
        border-radius: 12px;
        padding: 20px 30px;
        margin-bottom: 20px;
    }
    .briefing-box {
        background: #0a1628;
        border-left: 4px solid #ff4444;
        border-radius: 8px;
        padding: 20px;
        margin: 10px 0;
        font-size: 15px;
        line-height: 1.8;
    }
    .alert-box {
        background: #1a0a0a;
        border-left: 4px solid #ff4444;
        border-radius: 8px;
        padding: 15px;
        margin: 8px 0;
    }
    .success-box {
        background: #0a1a0a;
        border-left: 4px solid #00cc44;
        border-radius: 8px;
        padding: 15px;
        margin: 8px 0;
    }
    .info-box {
        background: #0a1020;
        border-left: 4px solid #3399ff;
        border-radius: 8px;
        padding: 15px;
        margin: 8px 0;
    }
    .volunteer-card {
        background: #0d1b2a;
        border: 1px solid #1e3a5f;
        border-radius: 10px;
        padding: 15px;
        margin: 8px 0;
    }
    .chat-msg-user {
        background: #1a2a4a;
        border-radius: 10px;
        padding: 10px 15px;
        margin: 5px 0;
        text-align: right;
    }
    .chat-msg-ai {
        background: #0a1628;
        border-left: 3px solid #3399ff;
        border-radius: 10px;
        padding: 10px 15px;
        margin: 5px 0;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.6; }
        100% { opacity: 1; }
    }
    .critical-alert {
        background: linear-gradient(90deg, #4a0000, #2a0000);
        border: 2px solid #ff4444;
        border-radius: 10px;
        padding: 15px 25px;
        margin: 10px 0;
        animation: pulse 1.5s infinite;
        font-size: 18px;
        font-weight: bold;
        color: #ff4444;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ---- SESSION STATE ----
if "disasters"  not in st.session_state:
    st.session_state.disasters = []
if "volunteers" not in st.session_state:
    st.session_state.volunteers = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---- CITY COORDINATES (India) ----
CITY_COORDS = {
    "chennai":   (13.0827, 80.2707),
    "mumbai":    (19.0760, 72.8777),
    "delhi":     (28.6139, 77.2090),
    "kolkata":   (22.5726, 88.3639),
    "bangalore": (12.9716, 77.5946),
    "hyderabad": (17.3850, 78.4867),
    "pune":      (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
    "jaipur":    (26.9124, 75.7873),
    "kerala":    (10.8505, 76.2711),
    "gujarat":   (22.2587, 71.1924),
    "odisha":    (20.9517, 85.0985),
    "assam":     (26.2006, 92.9376),
    "uttarakhand":(30.0668, 79.0193),
    "manipur":   (24.6637, 93.9063),
}

def get_coords(location):
    key = location.lower().split(",")[0].strip()
    for city, coords in CITY_COORDS.items():
        if city in key:
            return coords
    return (20.5937, 78.9629)

# ---- CRITICAL ALERT BANNER ----
critical_disasters = [d for d in st.session_state.disasters
                      if d["assessment"]["risk_level"] == "Critical"]
if critical_disasters:
    for cd in critical_disasters:
        st.markdown(
            f'<div class="critical-alert">'
            f'🚨 CRITICAL ALERT — {cd["type"].upper()} AT '
            f'{cd["location"].upper()} | '
            f'RISK SCORE: {cd["assessment"]["risk_score"]}/100 | '
            f'IMMEDIATE ACTION REQUIRED'
            f'</div>',
            unsafe_allow_html=True
        )

# ---- HEADER ----
st.markdown("""
<div class="header-box">
    <h1 style="color:#ffffff; margin:0; font-size:32px;">
        🚨 DisasterAI — National Command Center
    </h1>
    <p style="color:#7fb3d3; margin:5px 0 0 0; font-size:15px;">
        Real-time Risk Assessment · Zero Hunger Optimizer · Smart Medic Queue ·
        Aqua-Flow Monitor · Eco-Logistics Router · Live Map · Volunteer Manager
    </p>
</div>
""", unsafe_allow_html=True)

# ---- SIDEBAR ----
with st.sidebar:
    st.markdown("## 📋 Report Disaster")
    disaster_type = st.selectbox("🌪 Disaster Type", DISASTER_TYPES)
    location      = st.text_input("📍 Location", placeholder="e.g. Chennai, Tamil Nadu")
    st.info("⚡ Severity is auto-detected by AI based on disaster type, location and population.")   
    population    = st.slider("👥 Affected Population",
                               min_value=100, max_value=500000,
                               value=5000, step=500)

    st.divider()
    assess_btn = st.button("🔍 Assess Risk & Allocate Resources",
                           use_container_width=True, type="primary")

    if assess_btn:
        if not location:
            st.error("⚠️ Please enter a location!")
        else:
            with st.spinner("🤖 AI analyzing disaster scenario..."):
                try:
                    result = assess_risk(disaster_type, location, population)
                    report = {
                        "id":        len(st.session_state.disasters) + 1,
                        "timestamp": datetime.now().strftime("%d %b %Y, %H:%M:%S"),
                        "type":      disaster_type,
                        "location":  location,
                        "severity":  result["severity"],
                        "population":population,
                        "coords":    result["coords"],
                        "assessment":result
                    }
                    # Show geographic warning if disaster not possible
                    if not result["geo_valid"]:
                        st.warning(result["geo_warning"])
                        st.info(f"💡 Possible disasters for this location: "
                                f"{', '.join(result['geo_alternatives'])}")
                    else:
                        st.session_state.disasters.append(report)
                        st.success("✅ Assessment complete!")
                        st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    st.divider()
    st.markdown("### 🖥️ System Status")
    st.success("🟢 AI Engine Online")
    st.info(f"📊 {len(st.session_state.disasters)} Active Incidents")
    st.info(f"👥 {len(st.session_state.volunteers)} Volunteers Registered")

# ---- METRICS ----
total       = len(st.session_state.disasters)
critical    = sum(1 for d in st.session_state.disasters
                  if d["assessment"]["risk_level"] == "Critical")
high        = sum(1 for d in st.session_state.disasters
                  if d["assessment"]["risk_level"] == "High")
avg_score   = round(sum(d["assessment"]["risk_score"]
                    for d in st.session_state.disasters) / total, 1) if total else 0
total_people= sum(d["population"] for d in st.session_state.disasters)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("📊 Total Incidents", total)
col2.metric("🔴 Critical",        critical)
col3.metric("🟠 High Risk",       high)
col4.metric("📈 Avg Risk Score",  f"{avg_score}/100")
col5.metric("👥 People Affected", f"{total_people:,}")

st.divider()

# ---- TABS ----
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "🚨 Command Center",
    "🗺️ Live Map",
    "🍱 Zero Hunger",
    "🏥 Smart Medic",
    "💧 Aqua-Flow",
    "👥 Volunteers",
    "🤖 AI Chatbot",
    "🌍 Live World Feed"
])

# ============================================================
# TAB 1 — COMMAND CENTER
# ============================================================
with tab1:
    if not st.session_state.disasters:
        st.markdown("""
        <div style="text-align:center; padding:60px; color:#7fb3d3;">
            <h2>👈 No Active Incidents</h2>
            <p>Use the sidebar to report a disaster and activate the AI engine.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.subheader("📡 Live Command Briefing")
        for d in st.session_state.disasters:
            a   = d["assessment"]
            r   = a["resources_needed"]
            line = (
                f"🔴 <b>Incident #{d['id']} — {d['type']} at {d['location']}</b> | "
                f"Risk: {a['risk_level']} ({a['risk_score']}/100) | "
                f"Population: {d['population']:,} | "
                f"Deploy: {r['rescue_teams']} rescue teams, "
                f"{r['medical_kits']:,} medical kits | "
                f"Response within: {a['estimated_response_time_hours']}h"
            )
            st.markdown(f'<div class="briefing-box">{line}</div>',
                        unsafe_allow_html=True)

        st.divider()
        chart_col, report_col = st.columns([1, 2])

        with chart_col:
            st.subheader("📊 Risk Score Overview")
            color_map  = {"Critical":"#ff4444","High":"#ff8800",
                          "Medium":"#ffcc00","Low":"#00cc44"}
            chart_data = pd.DataFrame([{
                "Incident":   f"#{d['id']} {d['type']}",
                "Risk Score": d["assessment"]["risk_score"],
                "Risk Level": d["assessment"]["risk_level"]
            } for d in st.session_state.disasters])

            fig = px.bar(chart_data, x="Incident", y="Risk Score",
                         color="Risk Level", color_discrete_map=color_map,
                         range_y=[0,100], template="plotly_dark")
            fig.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                              paper_bgcolor="rgba(0,0,0,0)",
                              font_color="white")
            st.plotly_chart(fig, use_container_width=True)

            latest = st.session_state.disasters[-1]
            score  = latest["assessment"]["risk_score"]
            gauge  = go.Figure(go.Indicator(
                mode="gauge+number", value=score,
                title={"text": f"Latest: {latest['type']}",
                       "font": {"color":"white"}},
                gauge={
                    "axis":  {"range":[0,100],"tickcolor":"white"},
                    "bar":   {"color":"#ff4444" if score>79 else
                                      "#ff8800" if score>55 else
                                      "#ffcc00" if score>30 else "#00cc44"},
                    "steps": [
                        {"range":[0,30],  "color":"#003300"},
                        {"range":[30,55], "color":"#333300"},
                        {"range":[55,79], "color":"#332200"},
                        {"range":[79,100],"color":"#330000"},
                    ]
                }
            ))
            gauge.update_layout(paper_bgcolor="rgba(0,0,0,0)",
                                font_color="white", height=250)
            st.plotly_chart(gauge, use_container_width=True)

        with report_col:
            st.subheader("📋 Incident Reports")
            for disaster in reversed(st.session_state.disasters):
                a     = disaster["assessment"]
                emoji = {"Low":"🟢","Medium":"🟡",
                         "High":"🟠","Critical":"🔴"}.get(a["risk_level"],"⚪")
                with st.expander(
                    f"{emoji} #{disaster['id']} — {disaster['type']} | "
                    f"{disaster['location']} | {a['risk_level']} "
                    f"({a['risk_score']}/100)"
                ):
                    l, r = st.columns(2)
                    with l:
                        st.markdown("**🚨 Immediate Threats**")
                        for t in a["immediate_threats"]:
                            st.write(f"• {t}")
                        st.markdown("**✅ Recommended Actions**")
                        for act in a["recommended_actions"]:
                            st.write(f"• {act}")
                    with r:
                        res = a["resources_needed"]
                        st.markdown("**📦 Resources to Deploy**")
                        st.write(f"🏥 Medical Kits: **{res['medical_kits']:,}**")
                        st.write(f"🍱 Food Packages: **{res['food_packages']:,}**")
                        st.write(f"🏠 Shelter Units: **{res['shelter_units']:,}**")
                        st.write(f"🚑 Rescue Teams: **{res['rescue_teams']}**")
                        st.write(f"💧 Water: **{res['water_supply_liters']:,} L**")
                        st.write(f"⏱ Response: **{a['estimated_response_time_hours']}h**")

        st.divider()
        export_data = pd.DataFrame([{
            "ID": d["id"], "Timestamp": d["timestamp"],
            "Type": d["type"], "Location": d["location"],
            "Severity": d["severity"], "Population": d["population"],
            "Risk Level": d["assessment"]["risk_level"],
            "Risk Score": d["assessment"]["risk_score"],
            "Response Time (hrs)": d["assessment"]["estimated_response_time_hours"],
            "Medical Kits": d["assessment"]["resources_needed"]["medical_kits"],
            "Food Packages": d["assessment"]["resources_needed"]["food_packages"],
            "Shelter Units": d["assessment"]["resources_needed"]["shelter_units"],
            "Rescue Teams": d["assessment"]["resources_needed"]["rescue_teams"],
            "Water (L)": d["assessment"]["resources_needed"]["water_supply_liters"],
        } for d in st.session_state.disasters])

        st.download_button(
            label="⬇️ Download Full Incident Report (CSV)",
            data=export_data.to_csv(index=False),
            file_name=f"disaster_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv", use_container_width=True
        )

# ============================================================
# TAB 2 — LIVE MAP
# ============================================================
with tab2:
    st.subheader("🗺️ Live Disaster Map — India")
    st.markdown("*Every reported disaster is pinned in real time. Color = risk level.*")

    m = folium.Map(location=[20.5937, 78.9629], zoom_start=5,
                   tiles="CartoDB dark_matter")

    PIN_COLORS = {"Critical":"red","High":"orange",
                  "Medium":"beige","Low":"green"}

    if not st.session_state.disasters:
        st.info("👈 Report a disaster to see it appear on the map!")
    else:
        for d in st.session_state.disasters:
            a     = d["assessment"]
            color = PIN_COLORS.get(a["risk_level"], "blue")
            popup_html = f"""
            <div style='font-family:Arial; min-width:200px'>
                <h4 style='color:#ff4444'>#{d['id']} {d['type']}</h4>
                <b>Location:</b> {d['location']}<br>
                <b>Risk Level:</b> {a['risk_level']}<br>
                <b>Risk Score:</b> {a['risk_score']}/100<br>
                <b>Population:</b> {d['population']:,}<br>
                <b>Response Time:</b> {a['estimated_response_time_hours']}h<br>
                <hr>
                <b>Rescue Teams:</b> {a['resources_needed']['rescue_teams']}<br>
                <b>Medical Kits:</b> {a['resources_needed']['medical_kits']:,}<br>
                <b>Food Packages:</b> {a['resources_needed']['food_packages']:,}
            </div>
            """
            folium.Marker(
                location=d["coords"],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"#{d['id']} {d['type']} — {a['risk_level']}",
                icon=folium.Icon(color=color, icon="exclamation-sign",
                                 prefix="glyphicon")
            ).add_to(m)

            folium.Circle(
                location=d["coords"],
                radius=50000,
                color={"Critical":"#ff4444","High":"#ff8800",
                       "Medium":"#ffcc00","Low":"#00cc44"}.get(a["risk_level"],"blue"),
                fill=True, fill_opacity=0.15
            ).add_to(m)

    st_folium(m, width=None, height=550, returned_objects=[])

    if st.session_state.disasters:
        st.divider()
        st.subheader("📍 Active Incident Locations")
        map_data = pd.DataFrame([{
            "Incident": f"#{d['id']} {d['type']}",
            "Location": d["location"],
            "Risk Level": d["assessment"]["risk_level"],
            "Risk Score": d["assessment"]["risk_score"],
            "Coordinates": f"{d['coords'][0]:.2f}, {d['coords'][1]:.2f}"
        } for d in st.session_state.disasters])
        st.dataframe(map_data, use_container_width=True)

# ============================================================
# TAB 3 — ZERO HUNGER (PS1)
# ============================================================
with tab3:
    st.subheader("🍱 Zero Hunger — Food Resource Optimizer")
    st.markdown("*Calculates exact food requirements and prevents wastage during relief.*")
    st.divider()

    if not st.session_state.disasters:
        st.info("👈 Report a disaster first to activate the food optimizer.")
    else:
        total_food    = sum(d["assessment"]["resources_needed"]["food_packages"]
                            for d in st.session_state.disasters)
        total_pop     = sum(d["population"] for d in st.session_state.disasters)
        meals_per_day = total_pop * 3
        days_covered  = round(total_food / meals_per_day, 1) if meals_per_day else 0

        c1, c2, c3 = st.columns(3)
        c1.metric("🍱 Total Food Packages", f"{total_food:,}")
        c2.metric("🍽️ Meals Per Day Needed", f"{meals_per_day:,}")
        c3.metric("📅 Days of Supply",        f"{days_covered} days")

        st.divider()
        for d in st.session_state.disasters:
            fp         = d["assessment"]["resources_needed"]["food_packages"]
            pop        = d["population"]
            coverage   = round(fp / (pop * 3), 1) if pop else 0
            status     = "✅ Sufficient" if coverage >= 1 else "⚠️ Shortage Risk"
            box_class  = "success-box" if coverage >= 1 else "alert-box"
            st.markdown(
                f'<div class="{box_class}"><b>#{d["id"]} {d["type"]} — '
                f'{d["location"]}</b><br>'
                f'Food Packages: <b>{fp:,}</b> | Population: <b>{pop:,}</b> | '
                f'Coverage: <b>{coverage} days</b> | {status}</div>',
                unsafe_allow_html=True
            )

        st.divider()
        hunger_data = pd.DataFrame([{
            "Location":      d["location"],
            "Population":    d["population"],
            "Food Packages": d["assessment"]["resources_needed"]["food_packages"]
        } for d in st.session_state.disasters])
        fig2 = px.bar(hunger_data, x="Location",
                      y=["Population","Food Packages"],
                      barmode="group", template="plotly_dark",
                      title="Population vs Food Supply")
        fig2.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                           paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig2, use_container_width=True)

# ============================================================
# TAB 4 — SMART MEDIC (PS2)
# ============================================================
with tab4:
    st.subheader("🏥 Smart Medic — Emergency Queue Manager")
    st.markdown("*Prioritizes medical deployment based on AI risk scores.*")
    st.divider()

    if not st.session_state.disasters:
        st.info("👈 Report a disaster first to activate the medical queue.")
    else:
        sorted_d = sorted(st.session_state.disasters,
                          key=lambda x: x["assessment"]["risk_score"],
                          reverse=True)
        for rank, d in enumerate(sorted_d, 1):
            a   = d["assessment"]
            res = a["resources_needed"]
            emoji = {1:"🥇",2:"🥈",3:"🥉"}.get(rank, f"#{rank}")
            color = {"Critical":"#ff4444","High":"#ff8800",
                     "Medium":"#ffcc00","Low":"#00cc44"}.get(a["risk_level"],"white")
            st.markdown(
                f'<div class="info-box"><b style="font-size:18px">'
                f'{emoji} Priority {rank} — {d["type"]} at {d["location"]}</b><br>'
                f'<span style="color:{color}">Risk: {a["risk_level"]} '
                f'({a["risk_score"]}/100)</span> | Population: {d["population"]:,}<br>'
                f'🏥 Medical Kits: <b>{res["medical_kits"]:,}</b> | '
                f'🚑 Rescue Teams: <b>{res["rescue_teams"]}</b> | '
                f'⏱ Deploy within: <b>{a["estimated_response_time_hours"]}h</b>'
                f'</div>',
                unsafe_allow_html=True
            )

        st.divider()
        med_data = pd.DataFrame([{
            "Location":    d["location"],
            "Medical Kits":d["assessment"]["resources_needed"]["medical_kits"],
            "Rescue Teams":d["assessment"]["resources_needed"]["rescue_teams"],
            "Risk Score":  d["assessment"]["risk_score"]
        } for d in sorted_d])
        fig3 = px.scatter(med_data, x="Risk Score", y="Medical Kits",
                          size="Rescue Teams", color="Location",
                          template="plotly_dark",
                          title="Risk Score vs Medical Kits Required")
        fig3.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                           paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig3, use_container_width=True)

# ============================================================
# TAB 5 — AQUA-FLOW (PS4)
# ============================================================
with tab5:
    st.subheader("💧 Aqua-Flow — Water Supply Monitor")
    st.markdown("*Tracks water availability and triggers shortage alerts per zone.*")
    st.divider()

    SAFE_WATER = 15

    if not st.session_state.disasters:
        st.info("👈 Report a disaster first to activate the water monitor.")
    else:
        total_water  = sum(d["assessment"]["resources_needed"]["water_supply_liters"]
                           for d in st.session_state.disasters)
        total_needed = sum(d["population"] * SAFE_WATER
                           for d in st.session_state.disasters)
        water_gap    = total_needed - total_water

        c1, c2, c3 = st.columns(3)
        c1.metric("💧 Water Available", f"{total_water:,} L")
        c2.metric("🎯 Water Needed",    f"{total_needed:,} L")
        c3.metric("⚠️ Water Gap",
                  f"{max(0,water_gap):,} L",
                  delta="Shortage!" if water_gap > 0 else "Sufficient",
                  delta_color="inverse")

        st.divider()
        for d in st.session_state.disasters:
            water     = d["assessment"]["resources_needed"]["water_supply_liters"]
            needed    = d["population"] * SAFE_WATER
            gap       = needed - water
            pct       = round((water / needed) * 100, 1) if needed else 0
            status    = "✅ Safe" if gap <= 0 else "🚨 Shortage Alert"
            box_class = "success-box" if gap <= 0 else "alert-box"
            st.markdown(
                f'<div class="{box_class}"><b>#{d["id"]} {d["type"]} — '
                f'{d["location"]}</b><br>'
                f'Available: <b>{water:,} L</b> | Needed: <b>{needed:,} L</b> | '
                f'Coverage: <b>{pct}%</b> | {status}</div>',
                unsafe_allow_html=True
            )

        water_data = pd.DataFrame([{
            "Location":      d["location"],
            "Available (L)": d["assessment"]["resources_needed"]["water_supply_liters"],
            "Required (L)":  d["population"] * SAFE_WATER
        } for d in st.session_state.disasters])
        fig4 = px.bar(water_data, x="Location",
                      y=["Available (L)","Required (L)"],
                      barmode="group", template="plotly_dark",
                      color_discrete_map={"Available (L)":"#3399ff",
                                          "Required (L)":"#ff4444"},
                      title="Water Supply vs Demand per Zone")
        fig4.update_layout(plot_bgcolor="rgba(0,0,0,0)",
                           paper_bgcolor="rgba(0,0,0,0)", font_color="white")
        st.plotly_chart(fig4, use_container_width=True)

# ============================================================
# TAB 6 — VOLUNTEER MANAGER
# ============================================================
with tab6:
    st.subheader("👥 Volunteer Management System")
    st.markdown("*Register volunteers, match skills to disasters automatically.*")
    st.divider()

    SKILL_MATCH = {
        "Flood":      ["Swimmer", "Boat Operator", "Water Engineer"],
        "Earthquake": ["Structural Engineer", "Search & Rescue", "Doctor"],
        "Cyclone":    ["Electrician", "Search & Rescue", "Counselor"],
        "Fire":       ["Firefighter", "Doctor", "Paramedic"],
        "Landslide":  ["Heavy Machinery", "Search & Rescue", "Geologist"],
        "Drought":    ["Water Engineer", "Nutritionist", "Agronomist"],
        "Tsunami":    ["Swimmer", "Naval Officer", "Doctor"],
    }

    ALL_SKILLS = ["Doctor", "Paramedic", "Search & Rescue", "Firefighter",
                  "Water Engineer", "Structural Engineer", "Boat Operator",
                  "Swimmer", "Electrician", "Nutritionist", "Heavy Machinery",
                  "Counselor", "Naval Officer", "Geologist", "Agronomist"]

    with st.form("volunteer_form"):
        st.markdown("### ➕ Register New Volunteer")
        vc1, vc2, vc3 = st.columns(3)
        with vc1:
            v_name   = st.text_input("Full Name",    placeholder="e.g. Ravi Kumar")
        with vc2:
            v_skill  = st.selectbox("Primary Skill", ALL_SKILLS)
        with vc3:
            v_region = st.text_input("Region/City",  placeholder="e.g. Chennai")

        submitted = st.form_submit_button("✅ Register Volunteer",
                                          use_container_width=True)
        if submitted:
            if v_name and v_region:
                st.session_state.volunteers.append({
                    "id":     len(st.session_state.volunteers) + 1,
                    "name":   v_name,
                    "skill":  v_skill,
                    "region": v_region,
                    "status": "Available"
                })
                st.success(f"✅ {v_name} registered successfully!")
                st.rerun()
            else:
                st.error("Please fill in name and region!")

    st.divider()

    if st.session_state.volunteers:
        st.subheader(f"📋 Registered Volunteers ({len(st.session_state.volunteers)})")
        vol_df = pd.DataFrame(st.session_state.volunteers)
        st.dataframe(vol_df, use_container_width=True)

        if st.session_state.disasters:
            st.divider()
            st.subheader("🎯 AI Skill Matching — Volunteers to Disasters")
            st.markdown("*Automatically matches the right volunteer skills to each disaster type.*")

            for d in st.session_state.disasters:
                needed_skills = SKILL_MATCH.get(d["type"], [])
                matched = [v for v in st.session_state.volunteers
                           if v["skill"] in needed_skills]
                unmatched_count = d["assessment"]["resources_needed"]["rescue_teams"] - len(matched)

                with st.expander(
                    f"#{d['id']} {d['type']} at {d['location']} — "
                    f"{len(matched)} volunteers matched"
                ):
                    st.markdown(f"**Skills needed:** {', '.join(needed_skills)}")
                    if matched:
                        for v in matched:
                            st.markdown(
                                f'<div class="success-box">'
                                f'✅ <b>{v["name"]}</b> — {v["skill"]} | '
                                f'Region: {v["region"]}</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown(
                            '<div class="alert-box">'
                            '⚠️ No matching volunteers registered yet.</div>',
                            unsafe_allow_html=True
                        )
                    if unmatched_count > 0:
                        st.warning(f"⚠️ Still need {max(0,unmatched_count)} more "
                                   f"rescue team members for this incident.")
    else:
        st.info("No volunteers registered yet. Use the form above to add one!")

# ============================================================
# TAB 7 — AI CHATBOT
# ============================================================
with tab7:
    st.subheader("🤖 AI Command Assistant")
    st.markdown("*Ask anything about active disasters. Get instant intelligent answers.*")
    st.divider()

    def generate_answer(question, disasters, volunteers):
        q = question.lower()

        if not disasters:
            return ("No disasters have been reported yet. "
                    "Please report a disaster using the sidebar first.")

        total     = len(disasters)
        critical  = [d for d in disasters if d["assessment"]["risk_level"] == "Critical"]
        high      = [d for d in disasters if d["assessment"]["risk_level"] == "High"]
        top       = max(disasters, key=lambda x: x["assessment"]["risk_score"])
        total_pop = sum(d["population"] for d in disasters)
        total_med = sum(d["assessment"]["resources_needed"]["medical_kits"] for d in disasters)
        total_food= sum(d["assessment"]["resources_needed"]["food_packages"] for d in disasters)
        total_wat = sum(d["assessment"]["resources_needed"]["water_supply_liters"] for d in disasters)
        total_teams=sum(d["assessment"]["resources_needed"]["rescue_teams"] for d in disasters)

        if any(w in q for w in ["worst","dangerous","priority","first","critical"]):
            return (f"🔴 The highest priority incident is **#{top['id']} {top['type']} "
                    f"at {top['location']}** with a risk score of "
                    f"**{top['assessment']['risk_score']}/100** "
                    f"({top['assessment']['risk_level']} risk). "
                    f"Immediate response required within "
                    f"**{top['assessment']['estimated_response_time_hours']} hours**.")

        elif any(w in q for w in ["food","hunger","eat","meal"]):
            return (f"🍱 Total food packages needed across all incidents: "
                    f"**{total_food:,}**. "
                    f"This covers approximately "
                    f"**{round(total_food/(total_pop*3),1) if total_pop else 0} days** "
                    f"of meals for {total_pop:,} affected people.")

        elif any(w in q for w in ["water","aqua","drink","supply"]):
            return (f"💧 Total water supply allocated: **{total_wat:,} liters**. "
                    f"Minimum safe requirement is 15L per person per day. "
                    f"For {total_pop:,} people that's "
                    f"**{total_pop*15:,} liters needed per day**.")

        elif any(w in q for w in ["medical","doctor","hospital","kit","medic"]):
            return (f"🏥 Total medical kits deployed: **{total_med:,}** across "
                    f"**{total}** incidents. "
                    f"**{len(critical)}** incidents are Critical and need "
                    f"immediate medical attention.")

        elif any(w in q for w in ["volunteer","people","team","rescue"]):
            return (f"👥 **{total_teams}** rescue teams needed across all incidents. "
                    f"Currently **{len(volunteers)}** volunteers registered. "
                    f"{'Sufficient coverage.' if len(volunteers) >= total_teams else f'Need {total_teams - len(volunteers)} more volunteers urgently.'}")

        elif any(w in q for w in ["summary","overview","status","report","all"]):
            return (f"📊 **Command Center Summary:**\n\n"
                    f"• Total Incidents: **{total}**\n"
                    f"• Critical: **{len(critical)}** | High: **{len(high)}**\n"
                    f"• People Affected: **{total_pop:,}**\n"
                    f"• Medical Kits: **{total_med:,}**\n"
                    f"• Food Packages: **{total_food:,}**\n"
                    f"• Water Supply: **{total_wat:,} L**\n"
                    f"• Rescue Teams: **{total_teams}**\n"
                    f"• Volunteers: **{len(volunteers)}**")

        elif any(w in q for w in ["location","where","place","city"]):
            locations = ", ".join([f"{d['location']} ({d['type']})"
                                   for d in disasters])
            return f"📍 Active disaster locations: **{locations}**"

        else:
            return (f"🤖 I found **{total}** active incidents. "
                    f"The most urgent is **{top['type']} at {top['location']}** "
                    f"(Risk Score: {top['assessment']['risk_score']}/100). "
                    f"Try asking about: food, water, medical, volunteers, "
                    f"priority, or summary.")

    # Chat display
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-msg-user">👤 <b>You:</b> {msg["content"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f'<div class="chat-msg-ai">🤖 <b>DisasterAI:</b> {msg["content"]}</div>',
                unsafe_allow_html=True
            )

    st.divider()

    # Quick question buttons
    st.markdown("**💡 Quick Questions:**")
    qcol1, qcol2, qcol3, qcol4 = st.columns(4)
    with qcol1:
        if st.button("🔴 Worst incident?", use_container_width=True):
            q = "Which is the worst incident?"
            ans = generate_answer(q, st.session_state.disasters,
                                  st.session_state.volunteers)
            st.session_state.chat_history.append({"role":"user","content":q})
            st.session_state.chat_history.append({"role":"ai","content":ans})
            st.rerun()
    with qcol2:
        if st.button("📊 Full summary?", use_container_width=True):
            q = "Give me a full summary"
            ans = generate_answer(q, st.session_state.disasters,
                                  st.session_state.volunteers)
            st.session_state.chat_history.append({"role":"user","content":q})
            st.session_state.chat_history.append({"role":"ai","content":ans})
            st.rerun()
    with qcol3:
        if st.button("💧 Water status?", use_container_width=True):
            q = "What is the water supply status?"
            ans = generate_answer(q, st.session_state.disasters,
                                  st.session_state.volunteers)
            st.session_state.chat_history.append({"role":"user","content":q})
            st.session_state.chat_history.append({"role":"ai","content":ans})
            st.rerun()
    with qcol4:
        if st.button("👥 Volunteers?", use_container_width=True):
            q = "How many volunteers and rescue teams?"
            ans = generate_answer(q, st.session_state.disasters,
                                  st.session_state.volunteers)
            st.session_state.chat_history.append({"role":"user","content":q})
            st.session_state.chat_history.append({"role":"ai","content":ans})
            st.rerun()

    # Text input
    st.divider()
    user_input = st.text_input("💬 Ask anything about active disasters...",
                                placeholder="e.g. Which location needs help first?",
                                key="chat_input")
    send_col, clear_col = st.columns([3, 1])
    with send_col:
        if st.button("📤 Send", use_container_width=True, type="primary"):
            if user_input:
                ans = generate_answer(user_input, st.session_state.disasters,
                                      st.session_state.volunteers)
                st.session_state.chat_history.append(
                    {"role":"user","content":user_input})
                st.session_state.chat_history.append(
                    {"role":"ai","content":ans})
                st.rerun()
    with clear_col:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()
# ============================================================
# TAB 8 — LIVE WORLD FEED
# ============================================================
with tab8:
    st.subheader("🌍 Live Global Disaster Feed")
    st.markdown("*Real disasters happening around the world right now — updated live.*")
    st.divider()

    feed_col1, feed_col2 = st.columns(2)

    # ---- USGS EARTHQUAKES ----
    with feed_col1:
        st.markdown("### 🌍 Live Earthquakes — USGS")
        st.markdown("*Official US Geological Survey data — last 24 hours*")

        if st.button("🔄 Refresh Earthquake Data", use_container_width=True):
            st.rerun()

        with st.spinner("Fetching live earthquake data..."):
            quakes = fetch_usgs_earthquakes()

        if quakes:
            for q in quakes:
                st.markdown(
                    f'<div style="background:#0a1628; border-left: 4px solid '
                    f'{q["color"]}; border-radius:8px; padding:12px; margin:8px 0;">'
                    f'<b>🌍 M{q["magnitude"]} — {q["place"]}</b><br>'
                    f'<span style="color:{q["color"]}">⚠️ {q["severity"]}</span> | '
                    f'Depth: {q["depth_km"]} km | '
                    f'🕐 {q["time"]}</div>',
                    unsafe_allow_html=True
                )

            # Map of earthquakes
            st.divider()
            st.markdown("**🗺️ Earthquake Map — Last 24 Hours**")
            eq_map = folium.Map(location=[20, 0], zoom_start=2,
                                tiles="CartoDB dark_matter")
            for q in quakes:
                folium.CircleMarker(
                    location=[q["lat"], q["lon"]],
                    radius=max(4, q["magnitude"] * 3),
                    color=q["color"],
                    fill=True,
                    fill_opacity=0.7,
                    popup=folium.Popup(
                        f"<b>M{q['magnitude']} Earthquake</b><br>"
                        f"{q['place']}<br>"
                        f"Depth: {q['depth_km']} km<br>"
                        f"{q['time']}",
                        max_width=200
                    ),
                    tooltip=f"M{q['magnitude']} — {q['place']}"
                ).add_to(eq_map)
            st_folium(eq_map, width=None, height=400, returned_objects=[])
        else:
            st.warning("Could not fetch earthquake data. Check your internet connection.")

    # ---- GDACS GLOBAL DISASTERS ----
    with feed_col2:
        st.markdown("### 🌐 Global Disasters — GDACS")
        st.markdown("*Global Disaster Alert and Coordination System — live feed*")

        if st.button("🔄 Refresh Global Data", use_container_width=True):
            st.rerun()

        with st.spinner("Fetching global disaster alerts..."):
            gdacs_events = fetch_gdacs_disasters()

        if gdacs_events:
            for event in gdacs_events:
                st.markdown(
                    f'<div style="background:#0a1628; border-left: 4px solid '
                    f'{event["color"]}; border-radius:8px; padding:12px; margin:8px 0;">'
                    f'<b>{event["emoji"]} {event["title"]}</b><br>'
                    f'<span style="color:{event["color"]}">⚠️ Alert: '
                    f'{event["alert"]}</span><br>'
                    f'<small style="color:#7fb3d3">{event["summary"]}</small><br>'
                    f'<small>🕐 {event["date"]}</small>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.warning("Could not fetch GDACS data. Check your internet connection.")

    st.divider()
    st.markdown("""
    <div style="background:#0a1020; border:1px solid #1e3a5f;
    border-radius:8px; padding:15px; text-align:center; color:#7fb3d3;">
        📡 Data sources: USGS Earthquake Hazards Program ·
        GDACS Global Disaster Alert and Coordination System<br>
        🔄 Click refresh buttons to get latest data
    </div>
    """, unsafe_allow_html=True)