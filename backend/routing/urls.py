from django.urls import path

from .views import AnalyzeRoutesView

urlpatterns = [
    path("routes/analyze", AnalyzeRoutesView.as_view(), name="analyze-routes"),
]
