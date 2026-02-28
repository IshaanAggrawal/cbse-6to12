"""
Django settings for cbse_tutor project.
Supports local dev, Render (backend), Vercel (frontend).
"""

import os
from pathlib import Path
import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, ['localhost', '127.0.0.1']),
)

# Read .env only if it exists (not present on Render — env vars set in dashboard)
env_file = BASE_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(env_file)

SECRET_KEY = env('DJANGO_SECRET_KEY', default='cbse-tutor-insecure-dev-key-change-in-production')
DEBUG      = env('DEBUG', default=True)

# Render sets RENDER=true; allow the Render-assigned hostname automatically
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '0.0.0.0'])
if os.environ.get('RENDER'):
    RENDER_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '')
    if RENDER_HOSTNAME:
        ALLOWED_HOSTS.append(RENDER_HOSTNAME)


# ── Installed apps ────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'corsheaders',

    # Our apps
    'users',
    'tutor',
    'knowledge',
]

# ── Middleware ─────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',       # must be first
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cbse_tutor.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cbse_tutor.wsgi.application'


# ── Database — Render PostgreSQL or local SQLite ──────────────────────────────
DATABASES = {
    'default': env.db('DATABASE_URL', default=f'sqlite:///{BASE_DIR}/db.sqlite3')
}


# ── Django REST Framework ─────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.MultiPartParser',
        'rest_framework.parsers.FormParser',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon':  '60/minute',
        'user': '120/minute',
    },
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}


# ── CORS — allow local dev + deployed Vercel frontend ─────────────────────────
CORS_ALLOWED_ORIGINS = env.list(
    'CORS_ORIGINS',
    default=[
        'http://localhost:3000', 
        'http://127.0.0.1:3000', 
        'http://localhost:5173',
        'http://127.0.0.1:5173',
    ],
)
# Allow any *.vercel.app domain automatically
CORS_ALLOWED_ORIGIN_REGEXES = [
    r"^https://.*\.vercel\.app$",
]
CORS_ALLOW_CREDENTIALS = True


# ── Cache — Redis if REDIS_URL env var is set, else in-memory ─────────────────
REDIS_URL = os.environ.get('REDIS_URL', '')

if REDIS_URL:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'TIMEOUT': 3600,
        }
    }
else:
    # Works without Redis — cache is per-process, resets on restart
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'cbse-tutor-cache',
        }
    }


# ── Groq / LLM ────────────────────────────────────────────────────────────────
GROQ_API_KEY    = env('GROQ_API_KEY', default='')
PRIMARY_MODEL   = env('PRIMARY_MODEL',  default='llama-3.1-8b-instant')
VISION_MODEL    = env('VISION_MODEL',   default='meta-llama/llama-4-scout-17b-16e-instruct')
FALLBACK_MODEL  = env('FALLBACK_MODEL', default='gemma2-9b-it')
MAX_TOKENS      = env.int('MAX_TOKENS',   default=1024)
TEMPERATURE     = env.float('TEMPERATURE', default=0.1)


# ── Pinecone / Knowledge Base ─────────────────────────────────────────────────
PINECONE_API_KEY   = env('PINECONE_API_KEY',   default='')
PINECONE_INDEX     = env('PINECONE_INDEX_NAME', default='cbse-tutor')
EMBEDDING_MODEL    = env('EMBEDDING_MODEL',     default='all-MiniLM-L6-v2')
TOP_K_RETRIEVAL    = env.int('TOP_K_RETRIEVAL', default=5)
NCERT_PDF_DIR      = env('NCERT_PDF_DIR', default=str(BASE_DIR / 'knowledge-base/data/ncert_pdfs'))
SYLLABUS_DIR       = str(BASE_DIR / 'knowledge-base/data')
CHUNK_SIZE         = env.int('CHUNK_SIZE',   default=500)
CHUNK_OVERLAP      = env.int('CHUNK_OVERLAP', default=50)


# ── Static / Media ────────────────────────────────────────────────────────────
STATIC_URL  = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL   = '/media/'
MEDIA_ROOT  = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'Asia/Kolkata'
USE_I18N      = True
USE_TZ        = True

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {'format': '{asctime} [{levelname}] {name}: {message}', 'style': '{'},
    },
    'handlers': {
        'console': {'class': 'logging.StreamHandler', 'formatter': 'verbose'},
    },
    'root': {'handlers': ['console'], 'level': 'INFO'},
}
