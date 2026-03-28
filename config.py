"""
Configuration management for DisasterAI.
Centralizes all constants and tunable parameters.
"""

import os
from dataclasses import dataclass
from typing import Dict, List, Tuple

@dataclass
class DisasterConstants:
    """Disaster-related constants"""
    DISASTER_TYPES: List[str] = None
    THREATS: Dict[str, List[str]] = None
    ACTIONS: Dict[str, List[str]] = None
    DISASTER_BASE_RISK: Dict[str, int] = None

    def __post_init__(self):
        self.DISASTER_TYPES = [
            "Flood", "Earthquake", "Cyclone", "Fire",
            "Landslide", "Drought", "Tsunami"
        ]

        self.THREATS = {
            "Flood": [
                "Rising water levels",
                "Contaminated water supply",
                "Infrastructure collapse",
                "Disease outbreak risk"
            ],
            "Earthquake": [
                "Aftershocks expected",
                "Building collapses",
                "Gas line ruptures",
                "Trapped survivors"
            ],
            "Cyclone": [
                "High wind speeds",
                "Storm surge flooding",
                "Power outages",
                "Flying debris"
            ],
            "Fire": [
                "Rapid fire spread",
                "Toxic smoke inhalation",
                "Structural burns",
                "Evacuation bottlenecks"
            ],
            "Landslide": [
                "Road blockages",
                "Buried structures",
                "Secondary slides risk",
                "Utility line damage"
            ],
            "Drought": [
                "Acute water shortage",
                "Crop failure",
                "Livestock deaths",
                "Wildfires risk"
            ],
            "Tsunami": [
                "Coastal inundation",
                "Saltwater contamination",
                "Infrastructure destruction",
                "Multiple wave surges"
            ],
        }

        self.ACTIONS = {
            "Flood": [
                "Evacuate low-lying areas immediately",
                "Deploy water pumping units",
                "Set up relief camps on high ground",
                "Distribute clean drinking water"
            ],
            "Earthquake": [
                "Search and rescue operations",
                "Structural safety assessment",
                "Set up field hospitals",
                "Restore communication lines"
            ],
            "Cyclone": [
                "Issue evacuation orders for coastal areas",
                "Reinforce emergency shelters",
                "Pre-position rescue teams",
                "Secure loose infrastructure"
            ],
            "Fire": [
                "Deploy firefighting units immediately",
                "Establish firebreaks",
                "Evacuate surrounding areas",
                "Set up air quality monitoring"
            ],
            "Landslide": [
                "Clear blocked roads for access",
                "Evacuate unstable slopes",
                "Deploy heavy machinery",
                "Monitor for secondary slides"
            ],
            "Drought": [
                "Activate emergency water tankers",
                "Distribute food rations",
                "Set up cattle camps",
                "Implement water rationing policy"
            ],
            "Tsunami": [
                "Activate coastal early warning",
                "Full coastal evacuation",
                "Deploy naval rescue teams",
                "Set up inland relief centers"
            ],
        }

        self.DISASTER_BASE_RISK = {
            "Flood": 55,
            "Earthquake": 70,
            "Cyclone": 65,
            "Fire": 50,
            "Landslide": 45,
            "Drought": 35,
            "Tsunami": 80,
        }


@dataclass
class GeographicConstants:
    """Geographic intelligence database"""
    GEOGRAPHY_DB: Dict[str, Dict] = None
    TERRAIN_DEFAULTS: Dict[str, Dict] = None
    HIGH_RISK_REGIONS: List[str] = None
    CITY_COORDS: Dict[str, Tuple[float, float]] = None
    DEFAULT_COORDS: Tuple[float, float] = (20.5937, 78.9629)  # India center

    def __post_init__(self):
        self.GEOGRAPHY_DB = {
            # COASTAL — Bay of Bengal
            "chennai": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Tsunami", "Earthquake", "Fire"], "impossible": ["Landslide", "Drought"]},
            "pondicherry": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Tsunami", "Earthquake", "Fire"], "impossible": ["Landslide", "Drought"]},
            "cuddalore": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Tsunami", "Earthquake"], "impossible": ["Landslide", "Drought"]},
            "nagapattinam": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Tsunami", "Earthquake"], "impossible": ["Landslide", "Drought"]},
            "rameswaram": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Tsunami", "Earthquake"], "impossible": ["Landslide", "Drought"]},
            "tuticorin": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Tsunami", "Fire"], "impossible": ["Landslide"]},
            "kanyakumari": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Tsunami", "Earthquake"], "impossible": ["Drought"]},

            # COASTAL — Arabian Sea
            "mumbai": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Tsunami", "Earthquake", "Fire"], "impossible": ["Landslide", "Drought"]},
            "goa": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Tsunami", "Earthquake"], "impossible": ["Drought"]},
            "kochi": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Tsunami", "Earthquake"], "impossible": ["Drought", "Landslide"]},
            "kozhikode": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Tsunami", "Earthquake"], "impossible": ["Drought"]},
            "mangalore": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Tsunami", "Earthquake", "Landslide"], "impossible": ["Drought"]},
            "surat": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Earthquake", "Fire"], "impossible": ["Landslide"]},
            "visakhapatnam": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Tsunami", "Earthquake", "Fire"], "impossible": ["Landslide", "Drought"]},

            # INLAND PLAINS
            "salem": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "coimbatore": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought", "Landslide"], "impossible": ["Tsunami", "Cyclone"]},
            "erode": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "madurai": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "trichy": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "vellore": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "delhi": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "lucknow": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "kanpur": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "nagpur": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "hyderabad": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "bangalore": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone"]},
            "pune": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought", "Landslide"], "impossible": ["Tsunami", "Cyclone"]},
            "ahmedabad": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "bhopal": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "indore": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "jaipur": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "patna": {"terrain": "inland", "possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},

            # HILLY / MOUNTAIN
            "ooty": {"terrain": "mountain", "possible": ["Landslide", "Earthquake", "Flood", "Fire"], "impossible": ["Tsunami", "Cyclone", "Drought"]},
            "kodaikanal": {"terrain": "mountain", "possible": ["Landslide", "Earthquake", "Flood", "Fire"], "impossible": ["Tsunami", "Cyclone", "Drought"]},
            "munnar": {"terrain": "mountain", "possible": ["Landslide", "Earthquake", "Flood", "Fire"], "impossible": ["Tsunami", "Cyclone", "Drought"]},
            "shimla": {"terrain": "mountain", "possible": ["Landslide", "Earthquake", "Flood", "Fire"], "impossible": ["Tsunami", "Cyclone", "Drought"]},
            "manali": {"terrain": "mountain", "possible": ["Landslide", "Earthquake", "Flood", "Fire"], "impossible": ["Tsunami", "Cyclone", "Drought"]},
            "darjeeling": {"terrain": "mountain", "possible": ["Landslide", "Earthquake", "Flood", "Fire"], "impossible": ["Tsunami", "Cyclone", "Drought"]},
            "dehradun": {"terrain": "mountain", "possible": ["Landslide", "Earthquake", "Flood", "Fire"], "impossible": ["Tsunami", "Cyclone"]},
            "gangtok": {"terrain": "mountain", "possible": ["Landslide", "Earthquake", "Flood", "Fire"], "impossible": ["Tsunami", "Cyclone", "Drought"]},
            "uttarakhand": {"terrain": "mountain", "possible": ["Landslide", "Earthquake", "Flood", "Fire"], "impossible": ["Tsunami", "Cyclone", "Drought"]},
            "kashmir": {"terrain": "mountain", "possible": ["Landslide", "Earthquake", "Flood", "Fire"], "impossible": ["Tsunami", "Cyclone", "Drought"]},

            # DESERT / ARID
            "jaisalmer": {"terrain": "desert", "possible": ["Drought", "Fire", "Earthquake"], "impossible": ["Tsunami", "Cyclone", "Landslide", "Flood"]},
            "bikaner": {"terrain": "desert", "possible": ["Drought", "Fire", "Earthquake"], "impossible": ["Tsunami", "Cyclone", "Landslide", "Flood"]},
            "jodhpur": {"terrain": "desert", "possible": ["Drought", "Fire", "Earthquake", "Flood"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "kutch": {"terrain": "desert", "possible": ["Drought", "Earthquake", "Fire", "Flood"], "impossible": ["Tsunami", "Landslide"]},

            # NORTHEAST
            "guwahati": {"terrain": "river_plain", "possible": ["Flood", "Earthquake", "Landslide", "Fire"], "impossible": ["Tsunami", "Drought"]},
            "assam": {"terrain": "river_plain", "possible": ["Flood", "Earthquake", "Landslide", "Fire"], "impossible": ["Tsunami", "Drought"]},
            "manipur": {"terrain": "river_plain", "possible": ["Flood", "Earthquake", "Landslide", "Fire"], "impossible": ["Tsunami", "Cyclone", "Drought"]},
            "shillong": {"terrain": "mountain", "possible": ["Earthquake", "Landslide", "Flood", "Fire"], "impossible": ["Tsunami", "Cyclone", "Drought"]},
            "imphal": {"terrain": "river_plain", "possible": ["Flood", "Earthquake", "Landslide"], "impossible": ["Tsunami", "Cyclone", "Drought"]},
            "kolkata": {"terrain": "coastal", "possible": ["Flood", "Cyclone", "Earthquake", "Fire"], "impossible": ["Tsunami", "Drought", "Landslide"]},
        }

        self.TERRAIN_DEFAULTS = {
            "coastal": {"possible": ["Flood", "Cyclone", "Tsunami", "Earthquake", "Fire"], "impossible": ["Landslide", "Drought"]},
            "inland": {"possible": ["Flood", "Earthquake", "Fire", "Drought"], "impossible": ["Tsunami", "Cyclone", "Landslide"]},
            "mountain": {"possible": ["Landslide", "Earthquake", "Flood", "Fire"], "impossible": ["Tsunami", "Cyclone", "Drought"]},
            "desert": {"possible": ["Drought", "Fire", "Earthquake"], "impossible": ["Tsunami", "Cyclone", "Landslide", "Flood"]},
            "river_plain": {"possible": ["Flood", "Earthquake", "Landslide", "Fire"], "impossible": ["Tsunami", "Drought"]},
        }

        self.HIGH_RISK_REGIONS = [
            "japan", "indonesia", "philippines", "india", "bangladesh",
            "pakistan", "nepal", "haiti", "turkey", "iran", "china",
            "myanmar", "vietnam", "thailand", "chennai", "mumbai",
            "delhi", "kolkata", "kerala", "odisha", "assam"
        ]

        self.CITY_COORDS = {
            "chennai": (13.0827, 80.2707),
            "mumbai": (19.0760, 72.8777),
            "delhi": (28.6139, 77.2090),
            "kolkata": (22.5726, 88.3639),
            "bangalore": (12.9716, 77.5946),
            "hyderabad": (17.3850, 78.4867),
            "pune": (18.5204, 73.8567),
            "ahmedabad": (23.0225, 72.5714),
            "jaipur": (26.9124, 75.7873),
            "kerala": (10.8505, 76.2711),
            "gujarat": (22.2587, 71.1924),
            "odisha": (20.9517, 85.0985),
            "assam": (26.2006, 92.9376),
            "uttarakhand": (30.0668, 79.0193),
            "manipur": (24.6637, 93.9063),
        }


@dataclass
class ResourceConstants:
    """Resource allocation constants"""
    SAFE_WATER_LITERS_PER_PERSON_PER_DAY: int = 15
    MEALS_PER_PERSON_PER_DAY: int = 3
    RISK_LEVEL_MULTIPLIERS: Dict[str, float] = None
    RESPONSE_HOURS: Dict[str, int] = None

    def __post_init__(self):
        self.RISK_LEVEL_MULTIPLIERS = {
            "Low": 0.1,
            "Medium": 0.2,
            "High": 0.4,
            "Critical": 0.7
        }
        self.RESPONSE_HOURS = {
            "Low": 24,
            "Medium": 12,
            "High": 6,
            "Critical": 2
        }


@dataclass
class APIConstants:
    """External API configuration"""
    NOMINATIM_USER_AGENT: str = "disasterai_command_center"
    NOMINATIM_TIMEOUT: int = 10
    USGS_EARTHQUAKE_URL: str = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_day.geojson"
    GDACS_RSS_URL: str = "https://www.gdacs.org/xml/rss.xml"
    REQUEST_TIMEOUT: int = 10
    RETRY_ATTEMPTS: int = 3
    RETRY_DELAY: int = 2  # seconds
    CACHE_TTL: int = 300  # 5 minutes


@dataclass
class UIConstants:
    """User interface constants"""
    PAGE_TITLE: str = "DisasterAI — Command Center"
    PAGE_ICON: str = "🚨"
    DEFAULT_MAP_ZOOM: int = 5
    MAP_CENTER: Tuple[float, float] = (20.5937, 78.9629)
    PIN_COLORS: Dict[str, str] = None
    SEVERITY_COLORS: Dict[str, str] = None

    def __post_init__(self):
        self.PIN_COLORS = {
            "Critical": "red",
            "High": "orange",
            "Medium": "beige",
            "Low": "green"
        }
        self.SEVERITY_COLORS = {
            "Critical": "#ff4444",
            "High": "#ff8800",
            "Medium": "#ffcc00",
            "Low": "#00cc44"
        }


@dataclass
class DatabaseConstants:
    """Database configuration"""
    DATABASE_URL: str = "sqlite:///disasterai.db"
    ECHO_SQL: bool = False  # Set to True for debugging


# Singleton instances for easy import
disaster = DisasterConstants()
geographic = GeographicConstants()
resources = ResourceConstants()
api_config = APIConstants()
ui_config = UIConstants()
db_config = DatabaseConstants()


# Skill matching matrix
SKILL_MATCH = {
    "Flood": ["Swimmer", "Boat Operator", "Water Engineer"],
    "Earthquake": ["Structural Engineer", "Search & Rescue", "Doctor"],
    "Cyclone": ["Electrician", "Search & Rescue", "Counselor"],
    "Fire": ["Firefighter", "Doctor", "Paramedic"],
    "Landslide": ["Heavy Machinery", "Search & Rescue", "Geologist"],
    "Drought": ["Water Engineer", "Nutritionist", "Agronomist"],
    "Tsunami": ["Swimmer", "Naval Officer", "Doctor"],
}

ALL_SKILLS = [
    "Doctor", "Paramedic", "Search & Rescue", "Firefighter",
    "Water Engineer", "Structural Engineer", "Boat Operator",
    "Swimmer", "Electrician", "Nutritionist", "Heavy Machinery",
    "Counselor", "Naval Officer", "Geologist", "Agronomist"
]