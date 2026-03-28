"""
Risk Assessment Engine.
AI-powered disaster risk assessment with geographic validation.
"""

import random
from typing import Tuple, Dict, Any, List
from datetime import datetime

from config import disaster, resources
from .geographic import get_coords, validate_disaster, is_high_risk_region


def auto_detect_severity(
    disaster_type: str,
    location: str,
    population: int
) -> Tuple[str, str, int]:
    """
    Auto-determine severity based on disaster type, location and population.

    Args:
        disaster_type: Type of disaster
        location: Location name
        population: Affected population estimate

    Returns:
        Tuple of (severity, risk_level, score)
    """
    score = disaster.DISASTER_BASE_RISK.get(disaster_type, 50)

    # Boost score for high-risk regions
    if is_high_risk_region(location):
        score += 15

    # Population impact
    if population > 100000:
        score += 20
    elif population > 50000:
        score += 15
    elif population > 10000:
        score += 10
    elif population > 5000:
        score += 5

    # Add small random variation
    score += random.randint(-5, 10)
    score = min(99, max(10, score))

    # Determine severity level
    if score >= 80:
        severity = risk_level = "Critical"
    elif score >= 56:
        severity = risk_level = "High"
    elif score >= 31:
        severity = risk_level = "Medium"
    else:
        severity = risk_level = "Low"

    return severity, risk_level, score


def calculate_resource_needs(
    disaster_type: str,
    population: int,
    severity: str
) -> Dict[str, int]:
    """
    Calculate required resources based on population and severity.

    Args:
        population: Affected population
        severity: Severity level (Low, Medium, High, Critical)
        disaster_type: Type of disaster

    Returns:
        Dictionary with resource quantities
    """
    multiplier = resources.RISK_LEVEL_MULTIPLIERS[severity]

    medical_kits = int(population * multiplier * 0.5)
    food_packages = int(population * multiplier)
    shelter_units = int(population * multiplier * 0.3)
    rescue_teams = max(2, int(population * multiplier * 0.002))
    water_liters = int(population * multiplier * 10)

    return {
        "medical_kits": medical_kits,
        "food_packages": food_packages,
        "shelter_units": shelter_units,
        "rescue_teams": rescue_teams,
        "water_supply_liters": water_liters,
    }


def generate_threats_and_actions(disaster_type: str) -> Tuple[List[str], List[str]]:
    """
    Get random threats and recommended actions for a disaster type.

    Args:
        disaster_type: Type of disaster

    Returns:
        Tuple of (threats_list, actions_list)
    """
    threats = random.sample(disaster.THREATS.get(disaster_type, disaster.THREATS["Flood"]), 3)
    actions = random.sample(disaster.ACTIONS.get(disaster_type, disaster.ACTIONS["Flood"]), 3)
    return threats, actions


def get_priority_zones(location: str) -> List[str]:
    """
    Generate priority zones for response coordination.

    Args:
        location: Location name

    Returns:
        List of zone names
    """
    city = location.split(",")[0].strip()
    zones = [
        f"{city} Central District",
        f"{city} Riverside Zone",
        f"{city} Suburban Areas",
        f"{city} Industrial Zone"
    ]
    return zones


def assess_risk(
    disaster_type: str,
    location: str,
    population: int
) -> Dict[str, Any]:
    """
    Full AI risk assessment with geographic validation.

    Process:
    1. Validate disaster type against location geography
    2. Auto-detect severity based on multiple factors
    3. Calculate resource requirements
    4. Generate response recommendations

    Args:
        disaster_type: Type of disaster
        location: Location name
        population: Estimated affected population

    Returns:
        Comprehensive assessment dictionary
    """
    # Step 1: Validate geography
    is_valid, warning, alternatives = validate_disaster(disaster_type, location)

    # Step 2: Auto detect severity
    severity, risk_level, risk_score = auto_detect_severity(
        disaster_type, location, population
    )

    # Step 3: Calculate resources
    resources_needed = calculate_resource_needs(disaster_type, population, severity)

    # Step 4: Get threats and actions
    threats, actions = generate_threats_and_actions(disaster_type)

    # Step 5: Get priority zones
    priority_zones = get_priority_zones(location)

    # Step 6: Get coordinates
    coords = get_coords(location)

    # Step 7: Response time
    response_hours = resources.RESPONSE_HOURS[severity]

    return {
        "severity": severity,
        "risk_level": risk_level,
        "risk_score": risk_score,
        "immediate_threats": threats,
        "recommended_actions": actions,
        "geo_valid": is_valid,
        "geo_warning": warning,
        "geo_alternatives": alternatives,
        "resources_needed": resources_needed,
        "estimated_response_time_hours": response_hours,
        "priority_zones": priority_zones,
        "coords": coords,
    }