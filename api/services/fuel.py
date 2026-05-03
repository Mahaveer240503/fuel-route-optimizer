"""
fuel.py
-------
Core fuel-stop selection logic.

Steps:
1. Load the fuel-prices CSV once into a pandas DataFrame (cached in memory).
2. Given a route's total distance and the states along the route,
   divide the route into 500-mile segments.
3. For each segment, determine which states it passes through.
4. From those states, pick the station with the lowest retail price.
5. Return the list of selected fuel stops.

Key constants (configurable via settings):
  VEHICLE_RANGE_MILES = 500
  FUEL_EFFICIENCY_MPG = 10
"""

import logging
import math
from functools import lru_cache
from pathlib import Path

import pandas as pd
from django.conf import settings

logger = logging.getLogger(__name__)


# CSV Loading

@lru_cache(maxsize=1)
def _load_fuel_df() -> pd.DataFrame:
    """
    Load the fuel-prices CSV into a pandas DataFrame.
    Result is cached so the file is read only once per server lifetime.

    Filters to US-only stations (drops Canadian provinces like AB, BC, ON, etc.)
    """
    csv_path: Path = settings.FUEL_CSV_PATH
    logger.info(f"Loading fuel prices from {csv_path}")

    df = pd.read_csv(csv_path)

    # Rename columns to simpler names for convenience
    df = df.rename(columns={
        "OPIS Truckstop ID": "id",
        "Truckstop Name":    "name",
        "Address":           "address",
        "City":              "city",
        "State":             "state",
        "Rack ID":           "rack_id",
        "Retail Price":      "price",
    })

    # Strip whitespace from string columns (CSV has some extra spaces)
    df["city"]  = df["city"].str.strip()
    df["state"] = df["state"].str.strip()
    df["name"]  = df["name"].str.strip()

    # Keep only the 50 US states (drop Canadian provinces: AB, BC, MB, NB, NS, ON, QC, SK, YT)
    us_states = {
        "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA",
        "HI","ID","IL","IN","IA","KS","KY","LA","ME","MD",
        "MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
        "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC",
        "SD","TN","TX","UT","VT","VA","WA","WV","WI","WY",
    }
    df = df[df["state"].isin(us_states)].copy()

    # Drop rows with missing price
    df = df.dropna(subset=["price"])

    logger.info(f"Fuel CSV loaded: {len(df)} US stations across {df['state'].nunique()} states")
    return df


# ─── Fuel Stop Selection ──────────────────────────────────────────────────────

def _cheapest_station_in_states(df: pd.DataFrame, states: list[str]) -> dict | None:
    """
    From the DataFrame, find the single cheapest fuel station
    among the given list of state abbreviations.

    Returns a dict with station info, or None if no match found.
    """
    subset = df[df["state"].isin(states)]
        
    if subset.empty:
        return None

    # Find the row with the minimum retail price
    best = subset.loc[subset["price"].idxmin()]

    return {
        "location":  f"{best['name']}, {best['city']}, {best['state']}",
        "city":      best["city"],
        "state":     best["state"],
        "price":     round(float(best["price"]), 4),
    }

def select_fuel_stops(
    total_distance_miles: float,
    states_along_route: list[str],
) -> list[dict]:
    """
    Select optimal (cheapest) fuel stops for the entire route.

    Strategy:
    - The vehicle starts with a full tank (500-mile range).
    - Every 500 miles, we must refuel.
    - The route passes through `states_along_route` in order.
    - We map each 500-mile segment to a proportional slice of states.
    - Within that slice, we pick the cheapest station.

    Args:
        total_distance_miles: Total route distance in miles.
        states_along_route:   Ordered list of state abbreviations on the route.

    Returns:
        List of dicts: [{"location": str, "city": str, "state": str, "price": float}]
    """
    df = _load_fuel_df()

    vehicle_range = settings.VEHICLE_RANGE_MILES

    # How many fuel stops do we need?
    # We start with a full tank, so first stop is after 500 miles.
    # No stop needed if total distance ≤ 500 miles.
    num_stops = math.floor(total_distance_miles / vehicle_range)

    logger.info(
        f"Total distance: {total_distance_miles:.1f} miles → "
        f"{num_stops} fuel stop(s) required"
    )

    if num_stops == 0:
        logger.info("Route fits within one tank — no fuel stops needed.")
        return []

    # Divide the route into proportional segments.
    # Each stop corresponds to a segment of the route.
    #
    # Example: 1,200 miles with 2 stops:
    #   Stop 1 → around mile 500 (33% of route)
    #   Stop 2 → around mile 1000 (67% of route)
    #
    # We map each stop's position to a slice of the states list.
    num_states = len(states_along_route)
    fuel_stops = []

    for stop_num in range(1, num_stops + 1):
        # What fraction of the route is this stop at?
        stop_fraction = (stop_num * vehicle_range) / total_distance_miles
        stop_fraction = min(stop_fraction, 1.0)

        # Which states are relevant for this stop?
        # We look at the states around the stop position (+/- one segment).
        prev_fraction = ((stop_num - 1) * vehicle_range) / total_distance_miles

        start_idx = max(0,           int(prev_fraction * num_states))
        end_idx   = min(num_states,  int(stop_fraction * num_states) + 1)

        segment_states = states_along_route[start_idx:end_idx]
        
        logger.info(
            f"Stop {stop_num} (around mile {stop_num * vehicle_range:.0f}): "
            f"looking in states {segment_states}"
        )

        # Try to find a station in the segment states.
        # If not found, widen the search to all route states (fallback).
        station = _cheapest_station_in_states(df, segment_states)
        
        if station is None:
            logger.warning(
                f"No station found in {segment_states} for stop {stop_num}. "
                "Widening search to all route states."
            )
            station = _cheapest_station_in_states(df, states_along_route)

        if station is None:
            logger.warning(
                f"Still no station found for stop {stop_num} — skipping this stop."
            )
            continue

        # Avoid duplicate stops (same station selected for multiple segments)
        if station not in fuel_stops:
            fuel_stops.append(station)
            logger.info(
                f"  → Selected: {station['location']} @ ${station['price']:.4f}/gal"
            )
            
    return fuel_stops

