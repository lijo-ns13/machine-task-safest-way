"""Django settings. The API is stateless: no database, no auth, no sessions."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-only-insecure-key")
DEBUG = os.getenv("DJANGO_DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.getenv("DJANGO_ALLOWED_HOSTS", "*").split(",")

INSTALLED_APPS = [
    "corsheaders",
    "rest_framework",
    "routing",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {}  # nothing is persisted
TIME_ZONE = "UTC"
USE_TZ = True

# Frontend origins allowed to call the API (comma separated).
CORS_ALLOWED_ORIGINS = [
    o for o in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5173").split(",") if o
]

REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
}

# Third-party API configuration
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")
# Optional comma-separated ISO country codes to restrict geocoding, e.g. "us" or "in,us". Empty = worldwide.
GEOCODING_COUNTRY = os.getenv("GEOCODING_COUNTRY", "")
EXTERNAL_API_TIMEOUT = 20  # seconds

# Weather responses are cached so repeated searches don't hammer Open-Meteo.
CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
WEATHER_CACHE_SECONDS = 30 * 60
