from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import AnalyzeRequestSerializer
from .services import analyzer
from .services.errors import LocationNotFound, NoRouteFound, UpstreamError


class AnalyzeRoutesView(APIView):
    """POST /api/routes/analyze: the single endpoint the frontend needs."""

    def post(self, request):
        serializer = AnalyzeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # -> 400 with per-field errors
        data = serializer.validated_data

        try:
            result = analyzer.analyze(
                origin=data["origin"],
                destination=data["destination"],
                departure=data["departure_time"],
                load_lb=data["load_weight_lb"],
                interval_miles=data["checkpoint_interval_miles"],
            )
        except (LocationNotFound, NoRouteFound) as exc:
            return Response({"error": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
        except UpstreamError as exc:
            return Response({"error": str(exc)}, status=status.HTTP_502_BAD_GATEWAY)
        return Response(result)
