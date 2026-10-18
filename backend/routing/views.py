from rest_framework.response import Response
from rest_framework.views import APIView


class AnalyzeRoutesView(APIView):
    """Placeholder; implemented in a later commit."""

    def post(self, request):
        return Response({"detail": "not implemented"}, status=501)
