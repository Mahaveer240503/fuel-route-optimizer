"""
views.py
--------
The main API view for the Fuel Route Optimizer.

Endpoint: POST /api/route/

Orchestrates the full pipeline:
  1. Validate input (start + end city names)
  2. Geocode both cities → (lat, lon)
  3. Fetch driving route from OpenRouteService → distance + geometry
  4. Determine US states along the route (from geometry, no extra API calls)
  5. Select optimal (cheapest) fuel stops from the CSV
  6. Calculate total fuel cost
  7. Return structured JSON response
"""

import logging

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import RouteRequestSerializer
from .services.cost import calculate_total_cost
from .services.fuel import select_fuel_stops
from .services.geocoding import geocode_city
from .services.routing import get_route
from .services.us_states import sample_states_along_route

logger = logging.getLogger(__name__)


class RouteView(APIView):
    """
    POST /api/route/

    Request body (JSON):
        {
            "start": "Chicago, IL",
            "end":   "Houston, TX"
        }

    Response (JSON):
        {
            "start":       "Chicago, IL",
            "end":         "Houston, TX",
            "distance":    1092.3,
            "fuel_stops":  [
                {"location": "PILOT #123, Joplin, MO", "price": 3.07}
            ],
            "total_cost":  327.40
        }
    """

    def post(self, request: Request) -> Response:
        # ── Step 1: Validate Input ────────────────────────────────────────────
        serializer = RouteRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {"error": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        start_city = serializer.validated_data["start"]
        end_city   = serializer.validated_data["end"]

        logger.info(f"Route request: '{start_city}' → '{end_city}'")

        # ── Step 2: Geocode Both Cities ───────────────────────────────────────
        try:
            start_coords = geocode_city(start_city)   # (lat, lon)
            end_coords   = geocode_city(end_city)     # (lat, lon)
        except ValueError as e:
            logger.error(f"Geocoding failed: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ── Step 3: Fetch Route from ORS (1 external API call) ───────────────
        try:
            route = get_route(start_coords, end_coords)
        except ValueError as e:
            logger.error(f"Routing failed: {e}")
            return Response(
                {"error": str(e)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        distance_miles = route["distance_miles"]
        coordinates    = route["coordinates"]    # list of [lon, lat]

        # ── Step 4: Determine States Along the Route ──────────────────────────
        # Sample the route geometry to find which US states it passes through.
        # No additional API calls — purely local bounding-box matching.
        states_along_route = sample_states_along_route(coordinates)

        logger.info(f"States along route: {states_along_route}")

        if not states_along_route:
            logger.warning("Could not determine any states from route geometry.")

        # ── Step 5: Select Optimal Fuel Stops ────────────────────────────────
        fuel_stops = select_fuel_stops(distance_miles, states_along_route)

        # ── Step 6: Calculate Total Cost ─────────────────────────────────────
        cost_result = calculate_total_cost(distance_miles, fuel_stops)

        # ── Step 7: Build and Return Response ────────────────────────────────
        response_data = {
            "start":    start_city,
            "end":      end_city,
            "distance": round(distance_miles, 2),
            "fuel_stops": [
                {"location": stop["location"], "price": stop["price"]}
                for stop in fuel_stops
            ],
            "total_cost": cost_result["total_cost"],
            # Bonus fields for transparency (not required by spec but useful)
            "_meta": {
                "total_gallons":   cost_result["total_gallons"],
                "states_on_route": states_along_route,
                "cost_breakdown":  cost_result["cost_breakdown"],
            },
        }

        logger.info(
            f"Response: {distance_miles:.1f} miles, "
            f"{len(fuel_stops)} stop(s), "
            f"${cost_result['total_cost']:.2f} total"
        )

        return Response(response_data, status=status.HTTP_200_OK)
