import random
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

DISASTER_TYPES = ["Flood", "Earthquake", "Cyclone", "Fire", "Landslide", "Drought", "Tsunami"]

THREATS = {
    "Flood":      ["Rising water levels", "Contaminated water supply", "Infrastructure collapse", "Disease outbreak risk"],
    "Earthquake": ["Aftershocks expected", "Building collapses", "Gas line ruptures", "Trapped survivors"],
    "Cyclone":    ["High wind speeds", "Storm surge flooding", "Power outages", "Flying debris"],
    "Fire":       ["Rapid fire spread", "Toxic smoke inhalation", "Structural burns", "Evacuation bottlenecks"],
    "Landslide":  ["Road blockages", "Buried structures", "Secondary slides risk", "Utility line damage"],
    "Drought":    ["Acute water shortage", "Crop failure", "Livestock deaths", "Wildfires risk"],
    "Tsunami":    ["Coastal inundation", "Saltwater contamination", "Infrastructure destruction", "Multiple wave surges"],
}

ACTIONS = {
    "Flood":      ["Evacuate low-lying areas immediately", "Deploy water pumping units", "Set up relief camps on high ground", "Distribute clean drinking water"],
    "Earthquake": ["Search and rescue operations", "Structural safety assessment", "Set up field hospitals", "Restore communication lines"],
    "Cyclone":    ["Issue evacuation orders for coastal areas", "Reinforce emergency shelters", "Pre-position rescue teams", "Secure loose infrastructure"],
    "Fire":       ["Deploy firefighting units immediately", "Establish firebreaks", "Evacuate surrounding areas", "Set up air quality monitoring"],
    "Landslide":  ["Clear blocked roads for access", "Evacuate unstable slopes", "Deploy heavy machinery", "Monitor for secondary slides"],
    "Drought":    ["Activate emergency water tankers", "Distribute food rations", "Set up cattle camps", "Implement water rationing policy"],
    "Tsunami":    ["Activate coastal early warning", "Full coastal evacuation", "Deploy naval rescue teams", "Set up inland relief centers"],
}

# ---- GEOGRAPHIC INTELLIGENCE DATABASE ----
# Each region has: terrain type, possible disasters, impossible disasters
GEOGRAPHY_DB = {
    # COASTAL — Bay of Bengal
    "chennai":      {"terrain":"coastal",    "possible":["Flood","Cyclone","Tsunami","Earthquake","Fire"],          "impossible":["Landslide","Drought"]},
    "pondicherry":  {"terrain":"coastal",    "possible":["Flood","Cyclone","Tsunami","Earthquake","Fire"],          "impossible":["Landslide","Drought"]},
    "cuddalore":    {"terrain":"coastal",    "possible":["Flood","Cyclone","Tsunami","Earthquake"],                 "impossible":["Landslide","Drought"]},
    "nagapattinam": {"terrain":"coastal",    "possible":["Flood","Cyclone","Tsunami","Earthquake"],                 "impossible":["Landslide","Drought"]},
    "rameswaram":   {"terrain":"coastal",    "possible":["Flood","Cyclone","Tsunami","Earthquake"],                 "impossible":["Landslide","Drought"]},
    "tuticorin":    {"terrain":"coastal",    "possible":["Flood","Cyclone","Tsunami","Fire"],                       "impossible":["Landslide"]},
    "kanyakumari":  {"terrain":"coastal",    "possible":["Flood","Cyclone","Tsunami","Earthquake"],                 "impossible":["Drought"]},

    # COASTAL — Arabian Sea
    "mumbai":       {"terrain":"coastal",    "possible":["Flood","Cyclone","Tsunami","Earthquake","Fire"],          "impossible":["Landslide","Drought"]},
    "goa":          {"terrain":"coastal",    "possible":["Flood","Cyclone","Tsunami","Earthquake"],                 "impossible":["Drought"]},
    "kochi":        {"terrain":"coastal",    "possible":["Flood","Cyclone","Tsunami","Earthquake"],                 "impossible":["Drought","Landslide"]},
    "kozhikode":    {"terrain":"coastal",    "possible":["Flood","Cyclone","Tsunami","Earthquake"],                 "impossible":["Drought"]},
    "mangalore":    {"terrain":"coastal",    "possible":["Flood","Cyclone","Tsunami","Earthquake","Landslide"],     "impossible":["Drought"]},
    "surat":        {"terrain":"coastal",    "possible":["Flood","Cyclone","Earthquake","Fire"],                    "impossible":["Landslide"]},
    "visakhapatnam":{"terrain":"coastal",    "possible":["Flood","Cyclone","Tsunami","Earthquake","Fire"],          "impossible":["Landslide","Drought"]},

    # INLAND PLAINS — No tsunami, low landslide
    "salem":        {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "coimbatore":   {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought","Landslide"],        "impossible":["Tsunami","Cyclone"]},
    "erode":        {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "madurai":      {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "trichy":       {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "vellore":      {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "delhi":        {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "lucknow":      {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "kanpur":       {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "nagpur":       {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "hyderabad":    {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "bangalore":    {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone"]},
    "pune":         {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought","Landslide"],        "impossible":["Tsunami","Cyclone"]},
    "ahmedabad":    {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "bhopal":       {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "indore":       {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "jaipur":       {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "patna":        {"terrain":"inland",     "possible":["Flood","Earthquake","Fire","Drought"],                    "impossible":["Tsunami","Cyclone","Landslide"]},

    # HILLY / MOUNTAIN — Landslide heavy
    "ooty":         {"terrain":"mountain",   "possible":["Landslide","Earthquake","Flood","Fire"],                  "impossible":["Tsunami","Cyclone","Drought"]},
    "kodaikanal":   {"terrain":"mountain",   "possible":["Landslide","Earthquake","Flood","Fire"],                  "impossible":["Tsunami","Cyclone","Drought"]},
    "munnar":       {"terrain":"mountain",   "possible":["Landslide","Earthquake","Flood","Fire"],                  "impossible":["Tsunami","Cyclone","Drought"]},
    "shimla":       {"terrain":"mountain",   "possible":["Landslide","Earthquake","Flood","Fire"],                  "impossible":["Tsunami","Cyclone","Drought"]},
    "manali":       {"terrain":"mountain",   "possible":["Landslide","Earthquake","Flood","Fire"],                  "impossible":["Tsunami","Cyclone","Drought"]},
    "darjeeling":   {"terrain":"mountain",   "possible":["Landslide","Earthquake","Flood","Fire"],                  "impossible":["Tsunami","Cyclone","Drought"]},
    "dehradun":     {"terrain":"mountain",   "possible":["Landslide","Earthquake","Flood","Fire"],                  "impossible":["Tsunami","Cyclone"]},
    "gangtok":      {"terrain":"mountain",   "possible":["Landslide","Earthquake","Flood","Fire"],                  "impossible":["Tsunami","Cyclone","Drought"]},
    "uttarakhand":  {"terrain":"mountain",   "possible":["Landslide","Earthquake","Flood","Fire"],                  "impossible":["Tsunami","Cyclone","Drought"]},
    "kashmir":      {"terrain":"mountain",   "possible":["Landslide","Earthquake","Flood","Fire"],                  "impossible":["Tsunami","Cyclone","Drought"]},

    # DESERT / ARID — Drought heavy
    "jaisalmer":    {"terrain":"desert",     "possible":["Drought","Fire","Earthquake"],                            "impossible":["Tsunami","Cyclone","Landslide","Flood"]},
    "bikaner":      {"terrain":"desert",     "possible":["Drought","Fire","Earthquake"],                            "impossible":["Tsunami","Cyclone","Landslide","Flood"]},
    "jodhpur":      {"terrain":"desert",     "possible":["Drought","Fire","Earthquake","Flood"],                    "impossible":["Tsunami","Cyclone","Landslide"]},
    "kutch":        {"terrain":"desert",     "possible":["Drought","Earthquake","Fire","Flood"],                    "impossible":["Tsunami","Landslide"]},

    # NORTHEAST — Flood and earthquake prone
    "guwahati":     {"terrain":"river_plain","possible":["Flood","Earthquake","Landslide","Fire"],                  "impossible":["Tsunami","Drought"]},
    "assam":        {"terrain":"river_plain","possible":["Flood","Earthquake","Landslide","Fire"],                  "impossible":["Tsunami","Drought"]},
    "manipur":      {"terrain":"river_plain","possible":["Flood","Earthquake","Landslide","Fire"],                  "impossible":["Tsunami","Cyclone","Drought"]},
    "shillong":     {"terrain":"mountain",   "possible":["Earthquake","Landslide","Flood","Fire"],                  "impossible":["Tsunami","Cyclone","Drought"]},
    "imphal":       {"terrain":"river_plain","possible":["Flood","Earthquake","Landslide"],                         "impossible":["Tsunami","Cyclone","Drought"]},
    "kolkata":      {"terrain":"coastal",    "possible":["Flood","Cyclone","Earthquake","Fire"],                    "impossible":["Tsunami","Drought","Landslide"]},
}

# Default terrain types for unknown locations
TERRAIN_DEFAULTS = {
    "coastal":     {"possible":["Flood","Cyclone","Tsunami","Earthquake","Fire"],       "impossible":["Landslide","Drought"]},
    "inland":      {"possible":["Flood","Earthquake","Fire","Drought"],                 "impossible":["Tsunami","Cyclone","Landslide"]},
    "mountain":    {"possible":["Landslide","Earthquake","Flood","Fire"],               "impossible":["Tsunami","Cyclone","Drought"]},
    "desert":      {"possible":["Drought","Fire","Earthquake"],                         "impossible":["Tsunami","Cyclone","Landslide","Flood"]},
    "river_plain": {"possible":["Flood","Earthquake","Landslide","Fire"],               "impossible":["Tsunami","Drought"]},
}

# Disaster base risk scores
DISASTER_BASE_RISK = {
    "Flood":      55,
    "Earthquake": 70,
    "Cyclone":    65,
    "Fire":       50,
    "Landslide":  45,
    "Drought":    35,
    "Tsunami":    80,
}

HIGH_RISK_REGIONS = [
    "japan","indonesia","philippines","india","bangladesh",
    "pakistan","nepal","haiti","turkey","iran","china",
    "myanmar","vietnam","thailand","chennai","mumbai",
    "delhi","kolkata","kerala","odisha","assam"
]

# ---- COORDINATE CACHE ----
_coord_cache = {}

def get_coords(location):
    key = location.strip().lower()
    if key in _coord_cache:
        return _coord_cache[key]
    try:
        geolocator = Nominatim(user_agent="disasterai_app")
        loc = geolocator.geocode(location, timeout=5)
        if loc:
            coords = (loc.latitude, loc.longitude)
            _coord_cache[key] = coords
            return coords
    except GeocoderTimedOut:
        pass
    return (20.5937, 78.9629)

# ---- GEOGRAPHIC INTELLIGENCE ENGINE ----
def get_location_profile(location):
    """
    Returns the geographic profile of a location.
    Checks database first, then guesses terrain from keywords.
    """
    loc_lower = location.lower()

    # Check exact match in database
    for city, profile in GEOGRAPHY_DB.items():
        if city in loc_lower:
            return profile, city

    # Guess terrain from location name keywords
    coastal_keywords  = ["beach","coast","port","harbour","bay","island",
                         "sea","marina","nagar","puram","patnam","pattanam"]
    mountain_keywords = ["hill","mount","ooty","kodai","munnar","valley",
                         "peak","ridge","ghat","highland","nilgiri"]
    desert_keywords   = ["desert","jaisal","thar","arid","rann","kutch"]
    river_keywords    = ["river","nadi","ganga","brahmaputra","floods",
                         "delta","plains"]

    for kw in coastal_keywords:
        if kw in loc_lower:
            return TERRAIN_DEFAULTS["coastal"], "coastal region"

    for kw in mountain_keywords:
        if kw in loc_lower:
            return TERRAIN_DEFAULTS["mountain"], "mountain region"

    for kw in desert_keywords:
        if kw in loc_lower:
            return TERRAIN_DEFAULTS["desert"], "desert region"

    for kw in river_keywords:
        if kw in loc_lower:
            return TERRAIN_DEFAULTS["river_plain"], "river plain region"

    # Default to inland
    return TERRAIN_DEFAULTS["inland"], "inland region"

def validate_disaster(disaster_type, location):
    """
    Returns (is_valid, warning_message, suggested_alternatives)
    """
    profile, matched = get_location_profile(location)
    possible   = profile["possible"]
    impossible = profile["impossible"]

    if disaster_type in impossible:
        terrain = profile.get("terrain", "this region")
        warning = (
            f"⚠️ **Geographic Alert:** {disaster_type} is not geographically "
            f"possible at **{location}** (matched: {matched}). "
            f"This area is classified as **{terrain}** terrain."
        )
        return False, warning, possible

    return True, None, possible

def auto_detect_severity(disaster_type, location, population):
    """Auto determine severity based on disaster type, location and population."""
    score = DISASTER_BASE_RISK.get(disaster_type, 50)

    loc_lower = location.lower()
    for region in HIGH_RISK_REGIONS:
        if region in loc_lower:
            score += 15
            break

    if population > 100000:
        score += 20
    elif population > 50000:
        score += 15
    elif population > 10000:
        score += 10
    elif population > 5000:
        score += 5

    score += random.randint(-5, 10)
    score  = min(99, max(10, score))

    if score >= 80:
        severity = risk_level = "Critical"
    elif score >= 56:
        severity = risk_level = "High"
    elif score >= 31:
        severity = risk_level = "Medium"
    else:
        severity = risk_level = "Low"

    return severity, risk_level, score

# ---- MAIN ASSESSMENT ----
def assess_risk(disaster_type, location, population):
    """Full AI risk assessment with geographic validation."""

    # Step 1: Validate geography
    is_valid, warning, alternatives = validate_disaster(disaster_type, location)

    # Step 2: Auto detect severity
    severity, risk_level, risk_score = auto_detect_severity(
        disaster_type, location, population
    )

    multiplier     = {"Low":0.1,"Medium":0.2,"High":0.4,"Critical":0.7}[severity]
    medical_kits   = int(population * multiplier * 0.5)
    food_packages  = int(population * multiplier)
    shelter_units  = int(population * multiplier * 0.3)
    rescue_teams   = max(2, int(population * multiplier * 0.002))
    water_liters   = int(population * multiplier * 10)
    response_hours = {"Low":24,"Medium":12,"High":6,"Critical":2}[severity]

    threats = random.sample(THREATS.get(disaster_type, THREATS["Flood"]), 3)
    actions = random.sample(ACTIONS.get(disaster_type, ACTIONS["Flood"]), 3)

    city = location.split(",")[0].strip()
    priority_zones = [
        f"{city} Central District",
        f"{city} Riverside Zone",
    ]

    coords = get_coords(location)

    return {
        "severity":              severity,
        "risk_level":            risk_level,
        "risk_score":            risk_score,
        "immediate_threats":     threats,
        "recommended_actions":   actions,
        "geo_valid":             is_valid,
        "geo_warning":           warning,
        "geo_alternatives":      alternatives,
        "resources_needed": {
            "medical_kits":        medical_kits,
            "food_packages":       food_packages,
            "shelter_units":       shelter_units,
            "rescue_teams":        rescue_teams,
            "water_supply_liters": water_liters,
        },
        "estimated_response_time_hours": response_hours,
        "priority_zones":        priority_zones,
        "coords":                coords,
    }

# ---- REAL WORLD DATA FEEDS ----
import requests
import feedparser
from datetime import datetime

def fetch_usgs_earthquakes():
    try:
        url      = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
        response = requests.get(url, timeout=8)
        data     = response.json()
        quakes   = []
        for feature in data["features"][:15]:
            props  = feature["properties"]
            coords = feature["geometry"]["coordinates"]
            mag    = props.get("mag", 0)
            place  = props.get("place", "Unknown")
            time   = datetime.utcfromtimestamp(
                         props["time"] / 1000
                     ).strftime("%d %b %Y, %H:%M UTC")
            if mag >= 2.5:
                if mag >= 6.0:   severity, color = "Critical", "#ff4444"
                elif mag >= 5.0: severity, color = "High",     "#ff8800"
                elif mag >= 4.0: severity, color = "Medium",   "#ffcc00"
                else:            severity, color = "Low",      "#00cc44"

                quakes.append({
                    "type":      "Earthquake",
                    "place":     place,
                    "magnitude": mag,
                    "severity":  severity,
                    "color":     color,
                    "time":      time,
                    "lat":       coords[1],
                    "lon":       coords[0],
                    "depth_km":  coords[2],
                })
        return quakes
    except Exception:
        return []

def fetch_gdacs_disasters():
    try:
        feed   = feedparser.parse("https://www.gdacs.org/xml/rss.xml")
        events = []
        for entry in feed.entries[:15]:
            title   = entry.get("title",   "Unknown Event")
            summary = entry.get("summary", "")
            link    = entry.get("link",    "#")
            date    = entry.get("published","Recent")

            title_lower = title.lower()
            if "earthquake" in title_lower:   dtype, emoji = "Earthquake", "🌍"
            elif "flood"     in title_lower:  dtype, emoji = "Flood",      "🌊"
            elif any(w in title_lower for w in ["cyclone","hurricane","typhoon"]):
                                              dtype, emoji = "Cyclone",    "🌀"
            elif "fire"      in title_lower:  dtype, emoji = "Fire",       "🔥"
            elif "drought"   in title_lower:  dtype, emoji = "Drought",    "☀️"
            elif "tsunami"   in title_lower:  dtype, emoji = "Tsunami",    "🌊"
            elif "volcano"   in title_lower:  dtype, emoji = "Volcanic",   "🌋"
            else:                             dtype, emoji = "Disaster",   "⚠️"

            if   "red"    in title_lower or "red"    in summary.lower(): alert, color = "Critical", "#ff4444"
            elif "orange" in title_lower or "orange" in summary.lower(): alert, color = "High",     "#ff8800"
            elif "green"  in title_lower or "green"  in summary.lower(): alert, color = "Low",      "#00cc44"
            else:                                                         alert, color = "Medium",   "#ffcc00"

            events.append({
                "title":   title,
                "type":    dtype,
                "emoji":   emoji,
                "summary": summary[:200] + "..." if len(summary) > 200 else summary,
                "alert":   alert,
                "color":   color,
                "date":    date,
                "link":    link,
            })
        return events
    except Exception:
        return []