"""
Reusable Streamlit UI Components.
Provides consistent styling and component functions.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from typing import List, Dict, Any

from config import ui_config


def set_page_config():
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title=ui_config.PAGE_TITLE,
        page_icon=ui_config.PAGE_ICON,
        layout="wide"
    )


def apply_custom_css():
    """Apply custom CSS styling"""
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
        .warning-box {
            background: #1a1500;
            border-left: 4px solid #ffcc00;
            border-radius: 8px;
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
        .stButton>button {
            border-radius: 8px;
            transition: all 0.2s;
        }
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
        }
    </style>
    """, unsafe_allow_html=True)


def render_header():
    """Render the application header"""
    st.markdown(f"""
    <div class="header-box">
        <h1 style="color:#ffffff; margin:0; font-size:32px;">
            {ui_config.PAGE_ICON} DisasterAI — National Command Center
        </h1>
        <p style="color:#7fb3d3; margin:5px 0 0 0; font-size:15px;">
            Real-time Risk Assessment · Zero Hunger Optimizer · Smart Medic Queue ·
            Aqua-Flow Monitor · Eco-Logistics Router · Live Map · Volunteer Manager
        </p>
    </div>
    """, unsafe_allow_html=True)


def render_critical_alert_banner(disasters: List[Any]):
    """Render alert banner for critical disasters"""
    critical_disasters = [d for d in disasters if d.get("assessment", {}).get("risk_level") == "Critical"]

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


def render_metrics(disasters: List[Any]):
    """Render key metrics row"""
    total = len(disasters)
    critical = sum(1 for d in disasters if d.get("assessment", {}).get("risk_level") == "Critical")
    high = sum(1 for d in disasters if d.get("assessment", {}).get("risk_level") == "High")
    avg_score = sum(d.get("assessment", {}).get("risk_score", 0) for d in disasters)
    avg_score = round(avg_score / total, 1) if total else 0
    total_people = sum(d.get("population", 0) for d in disasters)

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📊 Total Incidents", total)
    col2.metric("🔴 Critical", critical)
    col3.metric("🟠 High Risk", high)
    col4.metric("📈 Avg Risk Score", f"{avg_score}/100")
    col5.metric("👥 People Affected", f"{total_people:,}")

    st.divider()


def render_risk_bar_chart(disasters: List[Any]):
    """Render bar chart showing risk scores"""
    if not disasters:
        return

    color_map = {"Critical": "#ff4444", "High": "#ff8800",
                 "Medium": "#ffcc00", "Low": "#00cc44"}

    chart_data = pd.DataFrame([{
        "Incident": f"#{d['id']} {d['type']}",
        "Risk Score": d["assessment"]["risk_score"],
        "Risk Level": d["assessment"]["risk_level"]
    } for d in reversed(disasters)])  # Show latest first

    fig = px.bar(chart_data, x="Incident", y="Risk Score",
                 color="Risk Level", color_discrete_map=color_map,
                 range_y=[0, 100], template="plotly_dark")
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        height=300
    )
    st.plotly_chart(fig, use_container_width=True)


def render_gauge_chart(disaster: Any):
    """Render gauge chart for latest incident"""
    score = disaster["assessment"]["risk_score"]

    gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        title={"text": f"Latest: {disaster['type']}", "font": {"color": "white"}},
        gauge={
            "axis": {"range": [0, 100], "tickcolor": "white"},
            "bar": {"color": "#ff4444" if score > 79 else
                    "#ff8800" if score > 55 else
                    "#ffcc00" if score > 30 else "#00cc44"},
            "steps": [
                {"range": [0, 30], "color": "#003300"},
                {"range": [30, 55], "color": "#333300"},
                {"range": [55, 79], "color": "#332200"},
                {"range": [79, 100], "color": "#330000"},
            ]
        }
    ))
    gauge.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font_color="white",
        height=250
    )
    st.plotly_chart(gauge, use_container_width=True)


def render_disaster_expander(disaster: Any):
    """Render expandable incident report"""
    a = disaster["assessment"]
    emoji = {"Low": "🟢", "Medium": "🟡", "High": "🟠", "Critical": "🔴"}.get(a["risk_level"], "⚪")

    with st.expander(
        f"{emoji} #{disaster['id']} — {disaster['type']} | "
        f"{disaster['location']} | {a['risk_level']} ({a['risk_score']}/100)"
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


def create_folium_map(disasters: List[Any], zoom_start: int = 5):
    """
    Create Folium map with disaster markers.

    Args:
        disasters: List of disaster records
        zoom_start: Initial zoom level

    Returns:
        Folium map object
    """
    import folium

    m = folium.Map(
        location=ui_config.MAP_CENTER,
        zoom_start=zoom_start,
        tiles="CartoDB dark_matter"
    )

    for d in disasters:
        a = d.get("assessment", {})
        risk_level = a.get("risk_level", "Medium")
        color = ui_config.PIN_COLORS.get(risk_level, "blue")

        popup_html = f"""
        <div style='font-family:Arial; min-width:200px'>
            <h4 style='color:#ff4444'>#{d['id']} {d['type']}</h4>
            <b>Location:</b> {d['location']}<br>
            <b>Risk Level:</b> {a.get('risk_level', 'N/A')}<br>
            <b>Risk Score:</b> {a.get('risk_score', 0)}/100<br>
            <b>Population:</b> {d.get('population', 0):,}<br>
            <b>Response Time:</b> {a.get('estimated_response_time_hours', 0)}h<br>
            <hr>
            <b>Rescue Teams:</b> {a.get('resources_needed', {}).get('rescue_teams', 0)}<br>
            <b>Medical Kits:</b> {a.get('resources_needed', {}).get('medical_kits', 0):,}<br>
            <b>Food Packages:</b> {a.get('resources_needed', {}).get('food_packages', 0):,}
        </div>
        """

        coords = d.get("coords", ui_config.MAP_CENTER)

        folium.Marker(
            location=coords,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"#{d['id']} {d['type']} — {risk_level}",
            icon=folium.Icon(color=color, icon="exclamation-sign", prefix="glyphicon")
        ).add_to(m)

        # Add radius circle
        radius_color = ui_config.SEVERITY_COLORS.get(risk_level, "#3399ff")
        folium.Circle(
            location=coords,
            radius=50000,
            color=radius_color,
            fill=True,
            fill_opacity=0.15
        ).add_to(m)

    return m


def render_empty_state(message: str = "No data available. Use the sidebar to add data."):
    """Render empty state placeholder"""
    st.markdown(f"""
    <div style="text-align:center; padding:60px; color:#7fb3d3;">
        <h2>👈 {message}</h2>
    </div>
    """, unsafe_allow_html=True)