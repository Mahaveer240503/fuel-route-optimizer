import requests
from django.conf import settings

ORS_GEOCODE_URL = "https://api.openrouteservice.org/geocode/search"

def geocode_city(city_name: str) -> tuple[float, float]:
    api_key = settings.ORS_API_KEY

    if not api_key:
        raise ValueError("ORS_API_KEY is not set")

    params = {
        "api_key": api_key,
        "text": city_name,
        "size": 1
    }

    try:
        response = requests.get(ORS_GEOCODE_URL, params=params, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise ValueError(f"ORS geocoding failed for '{city_name}': {e}")

    data = response.json()

    if not data["features"]:
        raise ValueError(f"Could not geocode '{city_name}'")

    coords = data["features"][0]["geometry"]["coordinates"]

    # ORS returns [lon, lat]
    lon, lat = coords

    return lat, lon