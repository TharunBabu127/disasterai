"""
UI Page renderers for each dashboard tab.
Each function renders content for a specific tab.
"""

import streamlit as st
import plotly.express as px
import pandas as pd
from typing import List, Dict

from config import geographic, resources, SKILL_MATCH, ALL_SKILLS
from core.risk_engine import assess_risk
from core.alerts import fetch_usgs_earthquakes, fetch_gdacs_disasters, clear_feed_caches
from ui.components import render_disaster_expander, render_gauge_chart, render_risk_bar_chart
from data.persistence import DisasterRepository, VolunteerRepository


def render_command_center(disaster_repo: DisasterRepository):
    """Render Command Center tab (Tab 1)"""
    st.subheader("📡 Live Command Briefing")

    disasters = disaster_repo.get_all()

    if not disasters:
        st.markdown("""
        <div style="text-align:center; padding:60px; color:#7fb3d3;">
            <h2>👈 No Active Incidents</h2>
            <p>Use the sidebar to report a disaster and activate the AI engine.</p>
        </div>
        """, unsafe_allow_html=True)
        return

    # Display all disasters briefing
    for d in disasters:
        a = d.assessment_dict if hasattr(d, 'assessment_dict') else d.to_dict()["assessment"]
        res = a.get("resources_needed", {})
        line = (
            f"🔴 <b>Incident #{d.id} — {d.type} at {d.location}</b> | "
            f"Risk: {a.get('risk_level', 'N/A')} ({a.get('risk_score', 0)}/100) | "
            f"Population: {d.population:,} | "
            f"Deploy: {res.get('rescue_teams', 0)} rescue teams, "
            f"{res.get('medical_kits', 0):,} medical kits | "
            f"Response within: {a.get('estimated_response_time_hours', 0)}h"
        )
        st.markdown(f'<div class="briefing-box">{line}</div>', unsafe_allow_html=True)

    st.divider()
    chart_col, report_col = st.columns([1, 2])

    with chart_col:
        st.subheader("📊 Risk Score Overview")
        render_risk_bar_chart([d.to_dict() for d in reversed(disasters)])

        if disasters:
            latest = disasters[-1]
            latest_dict = latest.to_dict()
            render_gauge_chart(latest_dict)

    with report_col:
        st.subheader("📋 Incident Reports")
        for disaster in reversed(disasters):
            render_disaster_expander(disaster.to_dict())

    st.divider()

    # Export functionality
    if disasters:
        export_data = pd.DataFrame([{
            "ID": d.id,
            "Timestamp": d.timestamp.strftime("%d %b %Y, %H:%M:%S") if d.timestamp else None,
            "Type": d.type,
            "Location": d.location,
            "Severity": d.severity,
            "Population": d.population,
            "Risk Level": d.risk_level,
            "Risk Score": d.risk_score,
            "Response Time (hrs)": d.estimated_response_time_hours,
            "Medical Kits": d.assessment_dict.get("resources_needed", {}).get("medical_kits", 0) if hasattr(d, 'assessment_dict') else 0,
            "Food Packages": d.assessment_dict.get("resources_needed", {}).get("food_packages", 0) if hasattr(d, 'assessment_dict') else 0,
            "Shelter Units": d.assessment_dict.get("resources_needed", {}).get("shelter_units", 0) if hasattr(d, 'assessment_dict') else 0,
            "Rescue Teams": d.assessment_dict.get("resources_needed", {}).get("rescue_teams", 0) if hasattr(d, 'assessment_dict') else 0,
            "Water (L)": d.assessment_dict.get("resources_needed", {}).get("water_supply_liters", 0) if hasattr(d, 'assessment_dict') else 0,
        } for d in disasters])

        st.download_button(
            label="⬇️ Download Full Incident Report (CSV)",
            data=export_data.to_csv(index=False),
            file_name=f"disaster_report_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )


def render_live_map(disaster_repo: DisasterRepository):
    """Render Live Map tab (Tab 2)"""
    st.subheader("🗺️ Live Disaster Map — India")
    st.markdown("*Every reported disaster is pinned in real time. Color = risk level.*")

    import folium
    from ui.components import create_folium_map
    from streamlit_folium import st_folium

    disasters = disaster_repo.get_all()
    m = create_folium_map([d.to_dict() for d in disasters], zoom_start=5)
    st_folium(m, width=None, height=550, returned_objects=[])

    if disasters:
        st.divider()
        st.subheader("📍 Active Incident Locations")
        map_data = pd.DataFrame([{
            "Incident": f"#{d.id} {d.type}",
            "Location": d.location,
            "Risk Level": d.risk_level,
            "Risk Score": d.risk_score,
            "Coordinates": f"{d.latitude:.2f}, {d.longitude:.2f}"
        } for d in disasters])
        st.dataframe(map_data, use_container_width=True)
    else:
        st.info("👈 Report a disaster to see it appear on the map!")


def render_zero_hunger(disaster_repo: DisasterRepository):
    """Render Zero Hunger food optimizer tab (Tab 3)"""
    st.subheader("🍱 Zero Hunger — Food Resource Optimizer")
    st.markdown("*Calculates exact food requirements and prevents wastage during relief.*")
    st.divider()

    disasters = disaster_repo.get_all()

    if not disasters:
        st.info("👈 Report a disaster first to activate the food optimizer.")
        return

    total_food = sum(
        d.assessment_dict.get("resources_needed", {}).get("food_packages", 0) if hasattr(d, 'assessment_dict') else 0
        for d in disasters
    )
    total_pop = sum(d.population for d in disasters)
    meals_per_day = total_pop * resources.MEALS_PER_PERSON_PER_DAY
    days_covered = round(total_food / meals_per_day, 1) if meals_per_day else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("🍱 Total Food Packages", f"{total_food:,}")
    c2.metric("🍽️ Meals Per Day Needed", f"{meals_per_day:,}")
    c3.metric("📅 Days of Supply", f"{days_covered} days")

    st.divider()

    for d in disasters:
        fp = d.assessment_dict.get("resources_needed", {}).get("food_packages", 0) if hasattr(d, 'assessment_dict') else 0
        pop = d.population
        coverage = round(fp / (pop * resources.MEALS_PER_PERSON_PER_DAY), 1) if pop else 0
        status = "✅ Sufficient" if coverage >= 1 else "⚠️ Shortage Risk"
        box_class = "success-box" if coverage >= 1 else "alert-box"

        st.markdown(
            f'<div class="{box_class}"><b>#{d.id} {d.type} — {d.location}</b><br>'
            f'Food Packages: <b>{fp:,}</b> | Population: <b>{pop:,}</b> | '
            f'Coverage: <b>{coverage} days</b> | {status}</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # Chart
    hunger_data = pd.DataFrame([{
        "Location": d.location,
        "Population": d.population,
        "Food Packages": d.assessment_dict.get("resources_needed", {}).get("food_packages", 0) if hasattr(d, 'assessment_dict') else 0
    } for d in disasters])

    if len(hunger_data) > 0:
        fig2 = px.bar(hunger_data, x="Location",
                      y=["Population", "Food Packages"],
                      barmode="group",
                      template="plotly_dark",
                      title="Population vs Food Supply")
        fig2.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white"
        )
        st.plotly_chart(fig2, use_container_width=True)


def render_smart_medic(disaster_repo: DisasterRepository):
    """Render Smart Medic priority queue tab (Tab 4)"""
    st.subheader("🏥 Smart Medic — Emergency Queue Manager")
    st.markdown("*Prioritizes medical deployment based on AI risk scores.*")
    st.divider()

    disasters = disaster_repo.get_all()

    if not disasters:
        st.info("👈 Report a disaster first to activate the medical queue.")
        return

    # Sort by risk score descending
    sorted_d = sorted(disasters, key=lambda x: x.risk_score, reverse=True)

    for rank, d in enumerate(sorted_d, 1):
        a = d.assessment_dict if hasattr(d, 'assessment_dict') else {}
        res = a.get("resources_needed", {})
        emoji = {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, f"#{rank}")
        color = {"Critical": "#ff4444", "High": "#ff8800",
                 "Medium": "#ffcc00", "Low": "#00cc44"}.get(d.risk_level, "white")

        st.markdown(
            f'<div class="info-box"><b style="font-size:18px">'
            f'{emoji} Priority {rank} — {d.type} at {d.location}</b><br>'
            f'<span style="color:{color}">Risk: {d.risk_level} ({d.risk_score}/100)</span> | '
            f'Population: {d.population:,}<br>'
            f'🏥 Medical Kits: <b>{res.get("medical_kits", 0):,}</b> | '
            f'🚑 Rescue Teams: <b>{res.get("rescue_teams", 0)}</b> | '
            f'⏱ Deploy within: <b>{a.get("estimated_response_time_hours", 0)}h</b>'
            f'</div>',
            unsafe_allow_html=True
        )

    st.divider()

    # Scatter plot
    med_data = pd.DataFrame([{
        "Location": d.location,
        "Medical Kits": d.assessment_dict.get("resources_needed", {}).get("medical_kits", 0) if hasattr(d, 'assessment_dict') else 0,
        "Rescue Teams": d.assessment_dict.get("resources_needed", {}).get("rescue_teams", 0) if hasattr(d, 'assessment_dict') else 0,
        "Risk Score": d.risk_score
    } for d in sorted_d])

    if len(med_data) > 0:
        fig3 = px.scatter(med_data, x="Risk Score", y="Medical Kits",
                          size="Rescue Teams", color="Location",
                          template="plotly_dark",
                          title="Risk Score vs Medical Kits Required")
        fig3.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white"
        )
        st.plotly_chart(fig3, use_container_width=True)


def render_aqua_flow(disaster_repo: DisasterRepository):
    """Render Aqua-Flow water monitor tab (Tab 5)"""
    st.subheader("💧 Aqua-Flow — Water Supply Monitor")
    st.markdown("*Tracks water availability and triggers shortage alerts per zone.*")
    st.divider()

    SAFE_WATER = resources.SAFE_WATER_LITERS_PER_PERSON_PER_DAY
    disasters = disaster_repo.get_all()

    if not disasters:
        st.info("👈 Report a disaster first to activate the water monitor.")
        return

    total_water = sum(
        d.assessment_dict.get("resources_needed", {}).get("water_supply_liters", 0) if hasattr(d, 'assessment_dict') else 0
        for d in disasters
    )
    total_needed = sum(d.population * SAFE_WATER for d in disasters)
    water_gap = total_needed - total_water

    c1, c2, c3 = st.columns(3)
    c1.metric("💧 Water Available", f"{total_water:,} L")
    c2.metric("🎯 Water Needed", f"{total_needed:,} L")
    c3.metric("⚠️ Water Gap",
              f"{max(0, water_gap):,} L",
              delta="Shortage!" if water_gap > 0 else "Sufficient",
              delta_color="inverse")

    st.divider()

    for d in disasters:
        water = d.assessment_dict.get("resources_needed", {}).get("water_supply_liters", 0) if hasattr(d, 'assessment_dict') else 0
        needed = d.population * SAFE_WATER
        gap = needed - water
        pct = round((water / needed) * 100, 1) if needed else 0
        status = "✅ Safe" if gap <= 0 else "🚨 Shortage Alert"
        box_class = "success-box" if gap <= 0 else "alert-box"

        st.markdown(
            f'<div class="{box_class}"><b>#{d.id} {d.type} — {d.location}</b><br>'
            f'Available: <b>{water:,} L</b> | Needed: <b>{needed:,} L</b> | '
            f'Coverage: <b>{pct}%</b> | {status}</div>',
            unsafe_allow_html=True
        )

    # Chart
    water_data = pd.DataFrame([{
        "Location": d.location,
        "Available (L)": d.assessment_dict.get("resources_needed", {}).get("water_supply_liters", 0) if hasattr(d, 'assessment_dict') else 0,
        "Required (L)": d.population * SAFE_WATER
    } for d in disasters])

    if len(water_data) > 0:
        fig4 = px.bar(water_data, x="Location",
                      y=["Available (L)", "Required (L)"],
                      barmode="group",
                      template="plotly_dark",
                      color_discrete_map={"Available (L)": "#3399ff", "Required (L)": "#ff4444"},
                      title="Water Supply vs Demand per Zone")
        fig4.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font_color="white"
        )
        st.plotly_chart(fig4, use_container_width=True)


def render_volunteers(volunteer_repo: VolunteerRepository, disaster_repo: DisasterRepository):
    """Render Volunteer Management tab (Tab 6)"""
    st.subheader("👥 Volunteer Management System")
    st.markdown("*Register volunteers, match skills to disasters automatically.*")
    st.divider()

    disasters = disaster_repo.get_all()

    with st.form("volunteer_form"):
        st.markdown("### ➕ Register New Volunteer")
        vc1, vc2, vc3 = st.columns(3)
        with vc1:
            v_name = st.text_input("Full Name", placeholder="e.g. Ravi Kumar")
        with vc2:
            v_skill = st.selectbox("Primary Skill", ALL_SKILLS)
        with vc3:
            v_region = st.text_input("Region/City", placeholder="e.g. Chennai")

        submitted = st.form_submit_button("✅ Register Volunteer", use_container_width=True)
        if submitted:
            if v_name and v_region:
                volunteer_repo.create(name=v_name, skill=v_skill, region=v_region)
                st.success(f"✅ {v_name} registered successfully!")
                st.rerun()
            else:
                st.error("Please fill in name and region!")

    st.divider()

    volunteers = volunteer_repo.get_all()

    if volunteers:
        st.subheader(f"📋 Registered Volunteers ({len(volunteers)})")
        vol_df = pd.DataFrame([v.to_dict() for v in volunteers])
        # Remove registered_at column for display
        display_df = vol_df.drop(columns=["registered_at"], errors="ignore")
        st.dataframe(display_df, use_container_width=True)

        if disasters:
            st.divider()
            st.subheader("🎯 AI Skill Matching — Volunteers to Disasters")
            st.markdown("*Automatically matches the right volunteer skills to each disaster type.*")

            from config import SKILL_MATCH

            for d in disasters:
                d_dict = d.to_dict()
                needed_skills = SKILL_MATCH.get(d.type, [])
                matched = [v for v in volunteers if v.skill in needed_skills]
                unmatched_count = d_dict.get("assessment", {}).get("resources_needed", {}).get("rescue_teams", len(matched)) - len(matched)

                with st.expander(
                    f"#{d.id} {d.type} at {d.location} — "
                    f"{len(matched)} volunteers matched"
                ):
                    st.markdown(f"**Skills needed:** {', '.join(needed_skills)}")
                    if matched:
                        for v in matched:
                            st.markdown(
                                f'<div class="success-box">'
                                f'✅ <b>{v.name}</b> — {v.skill} | '
                                f'Region: {v.region}</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown(
                            '<div class="alert-box">'
                            '⚠️ No matching volunteers registered yet.</div>',
                            unsafe_allow_html=True
                        )
                    if unmatched_count > 0:
                        st.warning(f"⚠️ Still need {max(0, unmatched_count)} more "
                                   f"rescue team members for this incident.")
    else:
        st.info("No volunteers registered yet. Use the form above to add one!")


def render_ai_chatbot(disaster_repo: DisasterRepository, volunteer_repo: VolunteerRepository):
    """Render AI Chat Assistant tab (Tab 7)"""
    st.subheader("🤖 AI Command Assistant")
    st.markdown("*Ask anything about active disasters. Get instant intelligent answers.*")
    st.divider()

    # Initialize chat history in session state if not present
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    def generate_answer(question: str, disasters: List, volunteers: List) -> str:
        q = question.lower()

        if not disasters:
            return ("No disasters have been reported yet. "
                    "Please report a disaster using the sidebar first.")

        total = len(disasters)
        critical = [d for d in disasters if d.risk_level == "Critical"]
        high = [d for d in disasters if d.risk_level == "High"]
        top = max(disasters, key=lambda x: x.risk_score)
        total_pop = sum(d.population for d in disasters)
        total_med = sum(
            d.assessment_dict.get("resources_needed", {}).get("medical_kits", 0) if hasattr(d, 'assessment_dict') else 0
            for d in disasters
        )
        total_food = sum(
            d.assessment_dict.get("resources_needed", {}).get("food_packages", 0) if hasattr(d, 'assessment_dict') else 0
            for d in disasters
        )
        total_wat = sum(
            d.assessment_dict.get("resources_needed", {}).get("water_supply_liters", 0) if hasattr(d, 'assessment_dict') else 0
            for d in disasters
        )
        total_teams = sum(
            d.assessment_dict.get("resources_needed", {}).get("rescue_teams", 0) if hasattr(d, 'assessment_dict') else 0
            for d in disasters
        )

        if any(w in q for w in ["worst", "dangerous", "priority", "first", "critical"]):
            return (f"🔴 The highest priority incident is **#{top.id} {top.type} "
                    f"at {top.location}** with a risk score of "
                    f"**{top.risk_score}/100** "
                    f"({top.risk_level} risk). "
                    f"Immediate response required within "
                    f"**{top.assessment_dict.get('estimated_response_time_hours', 0)} hours**.")

        elif any(w in q for w in ["food", "hunger", "eat", "meal"]):
            return (f"🍱 Total food packages needed across all incidents: "
                    f"**{total_food:,}**. "
                    f"This covers approximately "
                    f"**{round(total_food / (total_pop * 3), 1) if total_pop else 0} days** "
                    f"of meals for {total_pop:,} affected people.")

        elif any(w in q for w in ["water", "aqua", "drink", "supply"]):
            from config import resources
            return (f"💧 Total water supply allocated: **{total_wat:,} liters**. "
                    f"Minimum safe requirement is {resources.SAFE_WATER_LITERS_PER_PERSON_PER_DAY}L per person per day. "
                    f"For {total_pop:,} people that's "
                    f"**{total_pop * resources.SAFE_WATER_LITERS_PER_PERSON_PER_DAY:,} liters needed per day**.")

        elif any(w in q for w in ["medical", "doctor", "hospital", "kit", "medic"]):
            return (f"🏥 Total medical kits deployed: **{total_med:,}** across "
                    f"**{total}** incidents. "
                    f"**{len(critical)}** incidents are Critical and need "
                    f"immediate medical attention.")

        elif any(w in q for w in ["volunteer", "people", "team", "rescue"]):
            vol_count = volunteers.count() if hasattr(volunteers, 'count') else len(volunteers)
            return (f"👥 **{total_teams}** rescue teams needed across all incidents. "
                    f"Currently **{vol_count}** volunteers registered. "
                    f"{'Sufficient coverage.' if vol_count >= total_teams else f'Need {total_teams - vol_count} more volunteers urgently.'}")

        elif any(w in q for w in ["summary", "overview", "status", "report", "all"]):
            return (f"📊 **Command Center Summary:**\n\n"
                    f"• Total Incidents: **{total}**\n"
                    f"• Critical: **{len(critical)}** | High: **{len(high)}**\n"
                    f"• People Affected: **{total_pop:,}**\n"
                    f"• Medical Kits: **{total_med:,}**\n"
                    f"• Food Packages: **{total_food:,}**\n"
                    f"• Water Supply: **{total_wat:,} L**\n"
                    f"• Rescue Teams: **{total_teams}**\n"
                    f"• Volunteers: **{len(volunteers)}**")

        elif any(w in q for w in ["location", "where", "place", "city"]):
            locations = ", ".join([f"{d.location} ({d.type})" for d in disasters])
            return f"📍 Active disaster locations: **{locations}**"

        else:
            return (f"🤖 I found **{total}** active incidents. "
                    f"The most urgent is **{top.type} at {top.location}** "
                    f"(Risk Score: {top.risk_score}/100). "
                    f"Try asking about: food, water, medical, volunteers, "
                    f"priority, or summary.")

    # Display chat history
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
            ans = generate_answer(q, disasters, volunteers)
            st.session_state.chat_history.append({"role": "user", "content": q})
            st.session_state.chat_history.append({"role": "ai", "content": ans})
            st.rerun()
    with qcol2:
        if st.button("📊 Full summary?", use_container_width=True):
            q = "Give me a full summary"
            ans = generate_answer(q, disasters, volunteers)
            st.session_state.chat_history.append({"role": "user", "content": q})
            st.session_state.chat_history.append({"role": "ai", "content": ans})
            st.rerun()
    with qcol3:
        if st.button("💧 Water status?", use_container_width=True):
            q = "What is the water supply status?"
            ans = generate_answer(q, disasters, volunteers)
            st.session_state.chat_history.append({"role": "user", "content": q})
            st.session_state.chat_history.append({"role": "ai", "content": ans})
            st.rerun()
    with qcol4:
        if st.button("👥 Volunteers?", use_container_width=True):
            q = "How many volunteers and rescue teams?"
            ans = generate_answer(q, disasters, volunteers)
            st.session_state.chat_history.append({"role": "user", "content": q})
            st.session_state.chat_history.append({"role": "ai", "content": ans})
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
                ans = generate_answer(user_input, disasters, volunteers)
                st.session_state.chat_history.append({"role": "user", "content": user_input})
                st.session_state.chat_history.append({"role": "ai", "content": ans})
                st.rerun()
    with clear_col:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()


def render_live_world_feed():
    """Render Live World Feed tab (Tab 8)"""
    st.subheader("🌍 Live Global Disaster Feed")
    st.markdown("*Real disasters happening around the world right now — updated live.*")
    st.divider()

    feed_col1, feed_col2 = st.columns(2)

    # USGS Earthquakes
    with feed_col1:
        st.markdown("### 🌍 Live Earthquakes — USGS")
        st.markdown("*Official US Geological Survey data — last 24 hours*")

        if st.button("🔄 Refresh Earthquake Data", use_container_width=True):
            clear_feed_caches()
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

            st.divider()
            st.markdown("**🗺️ Earthquake Map — Last 24 Hours**")
            import folium
            eq_map = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB dark_matter")
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
            from streamlit_folium import st_folium
            st_folium(eq_map, width=None, height=400, returned_objects=[])
        else:
            st.warning("Could not fetch earthquake data. Check your internet connection.")

    # GDACS Global Disasters
    with feed_col2:
        st.markdown("### 🌐 Global Disasters — GDACS")
        st.markdown("*Global Disaster Alert and Coordination System — live feed*")

        if st.button("🔄 Refresh Global Data", use_container_width=True):
            clear_feed_caches()
            st.rerun()

        with st.spinner("Fetching global disaster alerts..."):
            gdacs_events = fetch_gdacs_disasters()

        if gdacs_events:
            for event in gdacs_events:
                st.markdown(
                    f'<div style="background:#0a1628; border-left: 4px solid '
                    f'{event["color"]}; border-radius:8px; padding:12px; margin:8px 0;">'
                    f'<b>{event["emoji"]} {event["title"]}</b><br>'
                    f'<span style="color:{event["color"]}">⚠️ Alert: {event["alert"]}</span><br>'
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
