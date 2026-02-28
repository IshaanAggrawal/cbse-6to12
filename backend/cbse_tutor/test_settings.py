"""
cbse_tutor/test_settings.py — Minimal settings override for running tests.

Uses SQLite + in-memory cache so no Redis, Postgres, or external
services are needed. Run with:
    python manage.py test tutor --settings=cbse_tutor.test_settings
"""

from cbse_tutor.settings import *  # noqa: F401,F403

# SQLite in-memory — fast, no Postgres needed
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# In-memory cache — no Redis needed
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-cache",
    }
}
