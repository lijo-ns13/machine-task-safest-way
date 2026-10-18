from datetime import timedelta

from django.utils import timezone
from rest_framework import serializers

MAX_LOAD_LB = 80_000  # US federal gross weight limit
MAX_DAYS_AHEAD = 10  # keeps trip + 48h heatmap within Open-Meteo's 16-day forecast


class AnalyzeRequestSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=200)
    destination = serializers.CharField(max_length=200)
    departure_time = serializers.DateTimeField()
    load_weight_lb = serializers.IntegerField(min_value=0, max_value=MAX_LOAD_LB)
    checkpoint_interval_miles = serializers.ChoiceField(
        choices=[10, 25, 50], required=False, allow_null=True, default=None
    )

    def validate_departure_time(self, value):
        now = timezone.now()
        if value < now - timedelta(hours=1):
            raise serializers.ValidationError("Departure time cannot be in the past")
        if value > now + timedelta(days=MAX_DAYS_AHEAD):
            raise serializers.ValidationError(f"Forecasts are only reliable up to {MAX_DAYS_AHEAD} days ahead")
        return value

    def validate(self, attrs):
        if attrs["origin"].strip().lower() == attrs["destination"].strip().lower():
            raise serializers.ValidationError({"destination": "Destination must differ from origin"})
        return attrs
