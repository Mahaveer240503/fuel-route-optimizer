"""
us_states.py
------------
Approximate bounding boxes for all 50 US states.
Used to map a (lat, lon) coordinate to a state abbreviation without
making any external API calls.

Bounding boxes are [min_lat, max_lat, min_lon, max_lon].
Note: These are approximations — states have irregular borders.
The matching is "good enough" for fuel-stop filtering purposes.
"""

# State → [min_lat, max_lat, min_lon, max_lon]
STATE_BBOXES: dict[str, list[float]] = {
    "AL": [30.14, 35.01, -88.47, -84.89],
    "AK": [54.68, 71.54, -168.00, -129.99],
    "AZ": [31.33, 37.00, -114.82, -109.04],
    "AR": [33.00, 36.50, -94.62, -89.64],
    "CA": [32.53, 42.01, -124.41, -114.13],
    "CO": [36.99, 41.00, -109.06, -102.04],
    "CT": [40.95, 42.05, -73.73, -71.78],
    "DE": [38.45, 39.84, -75.79, -74.98],
    "FL": [24.55, 31.00, -87.63, -79.97],
    "GA": [30.36, 35.00, -85.61, -80.84],
    "HI": [18.91, 28.40, -160.25, -154.80],
    "ID": [41.99, 49.00, -117.24, -111.04],
    "IL": [36.97, 42.51, -91.51, -87.02],
    "IN": [37.77, 41.76, -88.10, -84.78],
    "IA": [40.37, 43.50, -96.64, -90.14],
    "KS": [36.99, 40.00, -102.05, -94.59],
    "KY": [36.50, 39.15, -89.57, -81.96],
    "LA": [28.93, 33.02, -94.04, -88.82],
    "ME": [43.06, 47.46, -71.08, -66.95],
    "MD": [37.91, 39.72, -79.49, -75.05],
    "MA": [41.24, 42.89, -73.51, -69.93],
    "MI": [41.70, 48.19, -90.42, -82.41],
    "MN": [43.50, 49.38, -97.24, -89.48],
    "MS": [30.17, 35.00, -91.65, -88.10],
    "MO": [35.99, 40.61, -95.77, -89.10],
    "MT": [44.36, 49.00, -116.05, -104.04],
    "NE": [39.99, 43.00, -104.05, -95.31],
    "NV": [35.00, 42.00, -120.00, -114.04],
    "NH": [42.70, 45.31, -72.56, -70.61],
    "NJ": [38.93, 41.36, -75.56, -73.89],
    "NM": [31.33, 37.00, -109.05, -103.00],
    "NY": [40.50, 45.01, -79.76, -71.86],
    "NC": [33.84, 36.59, -84.32, -75.46],
    "ND": [45.94, 49.00, -104.05, -96.55],
    "OH": [38.40, 42.33, -84.82, -80.52],
    "OK": [33.62, 37.00, -103.00, -94.43],
    "OR": [41.99, 46.24, -124.56, -116.46],
    "PA": [39.72, 42.27, -80.52, -74.70],
    "RI": [41.15, 42.02, -71.86, -71.12],
    "SC": [32.04, 35.21, -83.35, -78.55],
    "SD": [42.49, 45.94, -104.06, -96.44],
    "TN": [34.98, 36.68, -90.31, -81.65],
    "TX": [25.84, 36.50, -106.65, -93.51],
    "UT": [36.99, 42.00, -114.05, -109.04],
    "VT": [42.73, 45.01, -73.44, -71.50],
    "VA": [36.54, 39.47, -83.68, -75.17],
    "WA": [45.54, 49.00, -124.73, -116.92],
    "WV": [37.20, 40.64, -82.64, -77.72],
    "WI": [42.49, 47.08, -92.89, -86.25],
    "WY": [40.99, 45.01, -111.06, -104.05],
}


def latlon_to_state(lat: float, lon: float) -> str | None:
    """
    Return the US state abbreviation for a given (lat, lon) coordinate.
    Uses bounding-box matching — approximate, not exact.

    Returns None if no state matches (e.g., ocean or Canada).
    """
    matches = []
    for state, (min_lat, max_lat, min_lon, max_lon) in STATE_BBOXES.items():
        if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
            matches.append(state)

    if not matches:
        return None

    # If multiple bounding boxes overlap (they do at borders),
    # return the one whose center is closest to the point.
    def center_distance(state: str) -> float:
        min_lat, max_lat, min_lon, max_lon = STATE_BBOXES[state]
        center_lat = (min_lat + max_lat) / 2
        center_lon = (min_lon + max_lon) / 2
        return (lat - center_lat) ** 2 + (lon - center_lon) ** 2

    return min(matches, key=center_distance)


def sample_states_along_route(coordinates: list[list[float]], num_samples: int = 50) -> list[str]:
    """
    Given a list of [lon, lat] route coordinates from ORS,
    sample evenly and return the unique states encountered (in order).

    Args:
        coordinates: List of [longitude, latitude] from ORS geometry
        num_samples: How many points to sample from the route

    Returns:
        Ordered list of unique state abbreviations along the route
    """
    if not coordinates:
        return []

    # Sample evenly spaced indices
    total = len(coordinates)
    step = max(1, total // num_samples)
    sampled = coordinates[::step]

    # Add the last point to ensure we always include the destination state
    if coordinates[-1] not in sampled:
        sampled.append(coordinates[-1])

    states_seen = []
    for lon, lat in sampled:
        state = latlon_to_state(lat, lon)
        if state and state not in states_seen:
            states_seen.append(state)

    return states_seen
