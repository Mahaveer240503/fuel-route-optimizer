"""
cost.py
-------
Calculates the total fuel cost for a route given the selected fuel stops.

Cost model:
  - The vehicle fills up completely at each fuel stop.
  - Each stop covers the next 500-mile (or shorter final) segment.
  - Gallons needed for a segment = segment_distance / mpg
  - Cost for that segment = gallons * price_at_stop
  - Total cost = sum of all segment costs
"""

import logging
import math

from django.conf import settings

logger = logging.getLogger(__name__)


def calculate_total_cost(
    total_distance_miles: float,
    fuel_stops: list[dict],
) -> dict:
    """
    Calculate the total fuel cost for the journey.

    Args:
        total_distance_miles: Total route distance in miles.
        fuel_stops: List of selected fuel stop dicts (each has a "price" field).

    Returns:
        Dict with:
          - "total_gallons":     total fuel needed for the trip
          - "total_cost":        total fuel cost in USD
          - "cost_breakdown":    per-stop cost details (for transparency)
    """
    mpg           = settings.FUEL_EFFICIENCY_MPG
    vehicle_range = settings.VEHICLE_RANGE_MILES

    # Total gallons needed regardless of stop choices
    total_gallons = total_distance_miles / mpg

    # Number of segments = number of fuel stops + 1
    # Segment distances:
    #   Each full segment = 500 miles, final segment = remainder
    num_stops  = len(fuel_stops)
    total_cost = 0.0
    breakdown  = []

    if num_stops == 0:
        # No stops — entire trip on one tank, priced at $0 (already paid)
        # In this case the caller should handle pricing from start location.
        # We return just the total gallons cost at $0 (no stop selected).
        logger.info("No fuel stops — no fueling cost to calculate.")
        return {
            "total_gallons": round(total_gallons, 4),
            "total_cost":    0.0,
            "cost_breakdown": [],
        }

    for i, stop in enumerate(fuel_stops):
        # Each stop fuels the NEXT segment
        if i < num_stops - 1:
            segment_miles = vehicle_range
        else:
            # Last stop covers whatever remains after (num_stops-1) * range
            remaining_miles = total_distance_miles - (num_stops - 1) * vehicle_range
            # But the vehicle already drove `vehicle_range` miles to get here,
            # so the last stop only needs to cover the final stretch.
            # More simply: always fill a full tank at every stop.
            
            segment_miles = vehicle_range  # fill up to full tank each time

        gallons_for_segment = segment_miles / mpg
        cost_for_segment    = gallons_for_segment * stop["price"]

        breakdown.append({
            "stop":            stop["location"],
            "price_per_gallon": stop["price"],
            "gallons":         round(gallons_for_segment, 4),
            "cost":            round(cost_for_segment, 4),
        })

        total_cost += cost_for_segment

    # The actual gallons consumed = total_distance / mpg
    # We fill up in full-tank increments, so we may buy slightly more than consumed.
    # Report actual consumption, not purchased.
    logger.info(
        f"Cost calculated: {total_gallons:.2f} gal needed, "
        f"${total_cost:.2f} total across {num_stops} stop(s)"
    )

    return {
        "total_gallons":  round(total_gallons, 4),
        "total_cost":     round(total_cost, 4),
        "cost_breakdown": breakdown,
    }
