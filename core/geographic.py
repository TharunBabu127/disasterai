"""
Geographic Intelligence Engine.
Provides location profiling, disaster validation, and geocoding services.
"""

from typing import Tuple, Optional, List, Dict
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import time
from functools import lru_cache

from config import geographic, api_config

# Coordinate cache (in-memory, persisted to database in future)
_coord_cache: Dict[str, Tuple[float, float]] = {}


def get_coords(location: str) -> Tuple[float, float]:
    """
    Get coordinates for a location with caching.
    Returns (latitude, longitude) or default coords on failure.

    Args:
        location: Location name string

    Returns:
        Tuple of (lat, lon)
    """
    key = location.strip().lower()

    # Check cache first
    if key in _coord_cache:
        return _coord_cache[key]

    # Check database cache in future implementation
    # For now, use hardcoded city coords
    for city, coords in geographic.CITY_COORDS.items():
        if city in key:
            _coord_cache[key] = coords
            return coords

    # Try geocoding with retry
    for attempt in range(api_config.RETRY_ATTEMPTS):
        try:
            geolocator = Nominatim(user_agent=api_config.NOMINATIM_USER_AGENT)
            loc = geolocator.geocode(location, timeout=api_config.NOMINATIM_TIMEOUT)
            if loc:
                coords = (loc.latitude, loc.longitude)
                _coord_cache[key] = coords
                return coords
        except (GeocoderTimedOut, GeocoderServiceError) as e:
            if attempt < api_config.RETRY_ATTEMPTS - 1:
                time.sleep(api_config.RETRY_DELAY * (2 ** attempt))  # Exponential backoff
                continue
            else:
                # Log error but don't expose to user
                print(f"Geocoding failed for '{location}': {e}")
        except Exception as e:
            print(f"Unexpected geocoding error for '{location}': {e}")

    # Return default coordinates (India center) - THIS IS A FALLBACK, should be logged
    print(f"WARNING: Using default coordinates for location '{location}' - geocoding failed")
    return geographic.DEFAULT_COORDS


def get_location_profile(location: str) -> Tuple[Dict, str]:
    """
    Returns the geographic profile of a location.
    Checks database first, then guesses terrain from keywords.

    Args:
        location: Location name string

    Returns:
        Tuple of (profile_dict, matched_name)
    """
    loc_lower = location.lower()

    # Check exact match in database
    for city, profile in geographic.GEOGRAPHY_DB.items():
        if city in loc_lower:
            return profile, city

    # Guess terrain from location name keywords
    coastal_keywords = ["beach", "coast", "port", "harbour", "bay", "island",
                       "sea", "marina", "nagar", "puram", "patnam", "pattanam"]
    mountain_keywords = ["hill", "mount", "ooty", "kodai", "munnar", "valley",
                         "peak", "ridge", "ghat", "highland", "nilgiri"]
    desert_keywords = ["desert", "jaisal", "thar", "arid", "rann", "kutch"]
    river_keywords = ["river", "nadi", "ganga", "brahmaputra", "floods",
                      "delta", "plains"]

    for kw in coastal_keywords:
        if kw in loc_lower:
            return geographic.TERRAIN_DEFAULTS["coastal"], "coastal region"

    for kw in mountain_keywords:
        if kw in loc_lower:
            return geographic.TERRAIN_DEFAULTS["mountain"], "mountain region"

    for kw in desert_keywords:
        if kw in loc_lower:
            return geographic.TERRAIN_DEFAULTS["desert"], "desert region"

    for kw in river_keywords:
        if kw in loc_lower:
            return geographic.TERRAIN_DEFAULTS["river_plain"], "river plain region"

    # Default to inland
    return geographic.TERRAIN_DEFAULTS["inland"], "inland region"


def validate_disaster(disaster_type: str, location: str) -> Tuple[bool, Optional[str], List[str]]:
    """
    Validate if a disaster type is geographically possible at a location.

    Args:
        disaster_type: Type of disaster (e.g., "Flood", "Earthquake")
        location: Location name

    Returns:
        Tuple of (is_valid, warning_message, suggested_alternatives)
    """
    profile, matched = get_location_profile(location)
    possible = profile["possible"]
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


def is_high_risk_region(location: str) -> bool:
    """
    Check if location is in a historically high-risk region.

    Args:
        location: Location name

    Returns:
        Boolean indicating if it's a high-risk region
    """
    loc_lower = location.lower()
    for region in geographic.HIGH_RISK_REGIONS:
        if region in loc_lower:
            return True
    return False


def get_nearby_cities(center: Tuple[float, float], radius_km: int = 100) -> List[str]:
    """
    Find nearby cities within radius (placeholder for future implementation).
    Would require a cities database or reverse geocoding.

    Args:
        center: (lat, lon) coordinates
        radius_km: Search radius in kilometers

    Returns:
        List of city names
    """
    # TODO: Implement with geopy reverse geocoding or cities database
    return []


def calculate_distance(coord1: Tuple[float, float], coord2: Tuple[float, float]) -> float:
    """
    Calculate distance between two coordinates using Haversine formula.

    Args:
        coord1: (lat1, lon1)
        coord2: (lat2, lon2)

    Returns:
        Distance in kilometers
    """
    from math import radians, sin, cos, sqrt, atan2

    lat1, lon1 = coord1
    lat2, lon2 = coord2

    R = 6371  # Earth's radius in km

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance