"""
serializers.py
--------------
DRF serializers for validating the API request input
and shaping the response output.
"""

from rest_framework import serializers


class RouteRequestSerializer(serializers.Serializer):
    """
    Validates the incoming POST request body.

    Expected JSON:
        {
            "start": "Chicago, IL",
            "end":   "Houston, TX"
        }
    """
    start = serializers.CharField(
        max_length=200,
        help_text="Starting city (e.g. 'Chicago, IL')",
    )
    end = serializers.CharField(
        max_length=200,
        help_text="Destination city (e.g. 'Houston, TX')",
    )

    def validate_start(self, value: str) -> str:
        return value.strip()

    def validate_end(self, value: str) -> str:
        return value.strip()

    def validate(self, data: dict) -> dict:
        if data["start"].lower() == data["end"].lower():
            raise serializers.ValidationError(
                "Start and end locations must be different."
            )
        return data


class FuelStopSerializer(serializers.Serializer):
    """Represents one fuel stop in the response."""
    location = serializers.CharField()
    price    = serializers.FloatField()


class RouteResponseSerializer(serializers.Serializer):
    """
    Shapes the final JSON response.

    Output:
        {
            "start":       "Chicago, IL",
            "end":         "Houston, TX",
            "distance":    1092.3,
            "fuel_stops":  [{"location": "...", "price": 3.12}],
            "total_cost":  327.40
        }
    """
    start      = serializers.CharField()
    end        = serializers.CharField()
    distance   = serializers.FloatField()
    fuel_stops = FuelStopSerializer(many=True)
    total_cost = serializers.FloatField()
