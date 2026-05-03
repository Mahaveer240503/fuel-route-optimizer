"""
Django settings for fuel_route project.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "django-insecure-change-me-in-production")

DEBUG = os.getenv("DEBUG", "True") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.contenttypes",
    "django.contrib.staticfiles",
    "rest_framework",
    "api",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "fuel_route.urls"

WSGI_APPLICATION = "fuel_route.wsgi.application"

# No database needed — all data comes from CSV + external API
DATABASES = {}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "/static/"

# ─── DRF config ──────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    # No authentication needed — this is a public API
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": [],
    "UNAUTHENTICATED_USER": None,
}

# ─── App-specific config ──────────────────────────────────────────────────────
# Path to the fuel-prices CSV (relative to BASE_DIR)
FUEL_CSV_PATH = BASE_DIR / "data" / "fuel_prices.csv"

# OpenRouteService API key — get a free key at https://openrouteservice.org/
ORS_API_KEY = os.getenv("ORS_API_KEY", "")

# Vehicle constraints
VEHICLE_RANGE_MILES = 500       # max miles per full tank
FUEL_EFFICIENCY_MPG = 10        # miles per gallon

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[{levelname}] {asctime} {name}: {message}",
            "style": "{",
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "api": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        }
    },
}
