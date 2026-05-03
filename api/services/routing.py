"""
routing.py
----------
Fetches the driving route between two (lat, lon) coordinate pairs
using the OpenRouteService (ORS) Directions API.

ORS is free — get a key at https://openrouteservice.org/dev/#/signup
Set it in your .env file as ORS_API_KEY.

This module makes exactly ONE external API call per route request.
"""

import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

ORS_DIRECTIONS_URL = "https://api.openrouteservice.org/v2/directions/driving-car/geojson"

# Conversion factor
METERS_PER_MILE = 1609.344


def get_route(
    start_coords: tuple[float, float],
    end_coords: tuple[float, float],
) -> dict:
    """
    Fetch the driving route between two points from OpenRouteService.

    Args:
        start_coords: (latitude, longitude) of the start city
        end_coords:   (latitude, longitude) of the end city

    Returns:
        A dict with:
          - "distance_miles": total route distance in miles (float)
          - "coordinates":    list of [lon, lat] points along the route
          - "duration_hours": estimated driving time in hours (float)

    Raises:
        ValueError: if ORS API key is missing or the API call fails
    """
    api_key = settings.ORS_API_KEY
    if not api_key:
        raise ValueError(
            "ORS_API_KEY is not set. "
            "Get a free key at https://openrouteservice.org/ and add it to your .env file."
        )

    # ORS expects coordinates as [longitude, latitude]
    start_lon_lat = [start_coords[1], start_coords[0]]
    end_lon_lat   = [end_coords[1],   end_coords[0]]

    payload = {
        "coordinates": [start_lon_lat, end_lon_lat],
        # Ask ORS for extra route details (distance, duration)
        "instructions": False,
    }

    headers = {
        "Authorization": api_key,
        "Content-Type": "application/json",
    }

    logger.info(
        f"Calling ORS Directions API: {start_coords} → {end_coords}"
    )

    try:
        response = requests.post(
            ORS_DIRECTIONS_URL,
            json=payload,
            headers=headers,
            timeout=30,
        )
        response.raise_for_status()
    except requests.HTTPError as e:
        # Surface the ORS error message for easier debugging
        try:
            error_detail = response.json()
        except Exception:
            error_detail = response.text
        raise ValueError(
            f"ORS API returned an error: {response.status_code} — {error_detail}"
        ) from e
    except requests.RequestException as e:
        raise ValueError(f"Failed to reach ORS API: {e}") from e

    data = response.json()

    # ORS GeoJSON response structure:
    # data["features"][0]["geometry"]["coordinates"] → list of [lon, lat]
    # data["features"][0]["properties"]["summary"]["distance"] → meters
    # data["features"][0]["properties"]["summary"]["duration"] → seconds
    try:
        feature    = data["features"][0]
        coordinates = feature["geometry"]["coordinates"]
        summary     = feature["properties"]["summary"]

        distance_meters = summary["distance"]
        duration_seconds = summary["duration"]
    except (KeyError, IndexError) as e:
        raise ValueError(f"Unexpected ORS response format: {e}. Response: {data}") from e

    distance_miles = distance_meters / METERS_PER_MILE
    duration_hours = duration_seconds / 3600

    logger.info(
        f"Route fetched: {distance_miles:.1f} miles, "
        f"{duration_hours:.1f} hours, "
        f"{len(coordinates)} route points"
    )

    return {
        "distance_miles": distance_miles,
        "coordinates": coordinates,   # list of [lon, lat]
        "duration_hours": duration_hours,
    }
