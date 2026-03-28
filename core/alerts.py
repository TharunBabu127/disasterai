"""
External API Feed Handlers.
Fetches real-time disaster data from external sources.
"""

import requests
import feedparser
from datetime import datetime
from typing import List, Dict, Any
import time
from functools import lru_cache

from config import api_config


def retry_on_failure(max_attempts: int = 3, delay: int = 2):
    """
    Decorator for retrying functions on failure with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        delay: Base delay in seconds (exponentially increased)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except (requests.RequestException, Exception) as e:
                    if attempt == max_attempts - 1:
                        print(f"ERROR: {func.__name__} failed after {max_attempts} attempts: {e}")
                        return []
                    wait_time = delay * (2 ** attempt)
                    time.sleep(wait_time)
            return []
        return wrapper
    return decorator


@retry_on_failure(max_attempts=api_config.RETRY_ATTEMPTS, delay=api_config.RETRY_DELAY)
@lru_cache(maxsize=1)
def fetch_usgs_earthquakes() -> List[Dict[str, Any]]:
    """
    Fetch recent earthquakes from USGS API.
    Results are cached for 5 minutes.

    Returns:
        List of earthquake dictionaries
    """
    try:
        response = requests.get(api_config.USGS_EARTHQUAKE_URL, timeout=api_config.REQUEST_TIMEOUT)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as e:
        print(f"Failed to fetch USGS data: {e}")
        return []
    except Exception as e:
        print(f"Error parsing USGS data: {e}")
        return []

    quakes = []
    for feature in data.get("features", [])[:15]:
        props = feature.get("properties", {})
        coords = feature.get("geometry", {}).get("coordinates", [0, 0, 0])

        mag = props.get("mag", 0)
        place = props.get("place", "Unknown")
        time_ts = props.get("time")

        if mag >= 2.5:
            if mag >= 6.0:
                severity, color = "Critical", "#ff4444"
            elif mag >= 5.0:
                severity, color = "High", "#ff8800"
            elif mag >= 4.0:
                severity, color = "Medium", "#ffcc00"
            else:
                severity, color = "Low", "#00cc44"

            # Format timestamp
            if time_ts:
                try:
                    time_str = datetime.utcfromtimestamp(time_ts / 1000).strftime("%d %b %Y, %H:%M UTC")
                except:
                    time_str = "Recent"
            else:
                time_str = "Recent"

            quakes.append({
                "type": "Earthquake",
                "place": place,
                "magnitude": mag,
                "severity": severity,
                "color": color,
                "time": time_str,
                "lat": coords[1] if len(coords) > 1 else 0,
                "lon": coords[0] if len(coords) > 0 else 0,
                "depth_km": coords[2] if len(coords) > 2 else 0,
            })

    return quakes


@retry_on_failure(max_attempts=api_config.RETRY_ATTEMPTS, delay=api_config.RETRY_DELAY)
@lru_cache(maxsize=1)
def fetch_gdacs_disasters() -> List[Dict[str, Any]]:
    """
    Fetch global disaster alerts from GDACS RSS feed.
    Results are cached for 5 minutes.

    Returns:
        List of disaster event dictionaries
    """
    try:
        feed = feedparser.parse(api_config.GDACS_RSS_URL)
        entries = feed.get("entries", [])
    except Exception as e:
        print(f"Failed to fetch GDACS data: {e}")
        return []

    events = []
    for entry in entries[:15]:
        title = entry.get("title", "Unknown Event")
        summary = entry.get("summary", "")
        link = entry.get("link", "#")
        date = entry.get("published", "Recent")

        title_lower = title.lower()

        # Detect disaster type
        if "earthquake" in title_lower:
            dtype, emoji = "Earthquake", "🌍"
        elif "flood" in title_lower:
            dtype, emoji = "Flood", "🌊"
        elif any(w in title_lower for w in ["cyclone", "hurricane", "typhoon"]):
            dtype, emoji = "Cyclone", "🌀"
        elif "fire" in title_lower:
            dtype, emoji = "Fire", "🔥"
        elif "drought" in title_lower:
            dtype, emoji = "Drought", "☀️"
        elif "tsunami" in title_lower:
            dtype, emoji = "Tsunami", "🌊"
        elif "volcano" in title_lower:
            dtype, emoji = "Volcanic", "🌋"
        else:
            dtype, emoji = "Disaster", "⚠️"

        # Detect alert level
        if "red" in title_lower or "red" in summary.lower():
            alert, color = "Critical", "#ff4444"
        elif "orange" in title_lower or "orange" in summary.lower():
            alert, color = "High", "#ff8800"
        elif "green" in title_lower or "green" in summary.lower():
            alert, color = "Low", "#00cc44"
        else:
            alert, color = "Medium", "#ffcc00"

        events.append({
            "title": title,
            "type": dtype,
            "emoji": emoji,
            "summary": summary[:200] + "..." if len(summary) > 200 else summary,
            "alert": alert,
            "color": color,
            "date": date,
            "link": link,
        })

    return events


def clear_feed_caches():
    """Clear cached API responses (useful for testing)"""
    fetch_usgs_earthquakes.cache_clear()
    fetch_gdacs_disasters.cache_clear()
    print("Feed caches cleared")