"""
Base settings for Phonix platform.
All shared configuration lives here.
Environment-specific overrides go in local.py / production.py.
"""

from pathlib import Path
from decouple import config, Csv
from celery.schedules import crontab

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-me-in-production')

DEBUG = False  # overridden per environment

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=Csv())

# ─── Applications ─────────────────────────────────────────────────────────────
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'django_celery_beat',
    'django_filters',
]

LOCAL_APPS = [
    'apps.core',
    'apps.accounts',
    'apps.wallets',
    'apps.transactions',
    'apps.trading',
    'apps.referral',
    'apps.incomes',
    'apps.ranks',
    'apps.dashboard',
    'apps.reports',
    'apps.support',
    'apps.kyc',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# ─── Middleware ────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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

WSGI_APPLICATION = 'config.wsgi.application'

# ─── Database — PostgreSQL with connection pooling ────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='phonix_db'),
        'USER': config('DB_USER', default='phonix_user'),
        'PASSWORD': config('DB_PASSWORD', default=''),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=60, cast=int),
        'OPTIONS': {
            'connect_timeout': 10,
        },
    }
}

# ─── Cache — Redis ─────────────────────────────────────────────────────────────
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'IGNORE_EXCEPTIONS': True,  # degrade gracefully if Redis is down
        },
        'TIMEOUT': 300,  # 5 minutes default
        'KEY_PREFIX': 'phonix',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# ─── Authentication ────────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'accounts.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'dashboard:index'
LOGOUT_REDIRECT_URL = 'accounts:login'

# ─── DRF Configuration ─────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'apps.core.pagination.StandardResultsPagination',
    'PAGE_SIZE': 20,
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# ─── Celery ────────────────────────────────────────────────────────────────────
CELERY_BROKER_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = config('REDIS_URL', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 300  # 5 minutes max per task
CELERY_WORKER_MAX_TASKS_PER_CHILD = 100

CELERY_BEAT_SCHEDULE = {
    # Daily ROI — Monday to Friday only at 00:00 UTC
    'daily-trade-roi': {
        'task': 'apps.trading.tasks.calculate_daily_roi',
        'schedule': crontab(hour=0, minute=0, day_of_week='mon-fri'),
    },
    # Weekly rank evaluation — Sunday 23:00 UTC
    'weekly-rank-evaluation': {
        'task': 'apps.ranks.tasks.evaluate_all_ranks',
        'schedule': crontab(hour=23, minute=0, day_of_week='sun'),
    },
    # Weekly rank payouts — Monday 01:00 UTC (after evaluation)
    'weekly-rank-payouts': {
        'task': 'apps.ranks.tasks.pay_weekly_rank_bonuses',
        'schedule': crontab(hour=1, minute=0, day_of_week='mon'),
    },
    # Weekly matching bonus — Monday 02:00 UTC
    'weekly-matching-bonus': {
        'task': 'apps.referral.tasks.calculate_weekly_matching_bonus',
        'schedule': crontab(hour=2, minute=0, day_of_week='mon'),
    },
    # Reset fresh binary volumes — Monday 00:30 UTC
    'reset-fresh-volumes': {
        'task': 'apps.referral.tasks.reset_fresh_volumes',
        'schedule': crontab(hour=0, minute=30, day_of_week='mon'),
    },
}

# ─── Internationalization ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ─── Static / Media ───────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Email ─────────────────────────────────────────────────────────────────────
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='Phonix <noreply@phonix.com>')

# ─── App-level Config ─────────────────────────────────────────────────────────
SITE_NAME = 'Phonix'
SITE_URL = config('SITE_URL', default='http://localhost:8000')
ADMIN_EMAIL = config('ADMIN_EMAIL', default='admin@phonix.com')

# Registration bonus given to every new user
REGISTRATION_BONUS_AMOUNT = 10.00
# Max % of registration bonus that can be used for a trade
REGISTRATION_BONUS_TRADE_LIMIT = 0.10

# Withdrawal constraints
WITHDRAWAL_MIN_AMOUNT = 10.00      # Minimum $10
WITHDRAWAL_FEE_PERCENT = 0.05     # 5% fee
WITHDRAWAL_RATE_LIMIT_HOURS = 24  # one withdrawal per 24 hours

# Dashboard cache TTL (seconds)
DASHBOARD_CACHE_TTL = 300

# ─── Logging ──────────────────────────────────────────────────────────────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} [{name}] {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'phonix.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO', 'propagate': False},
        'apps.wallets': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
        'apps.trading': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
        'apps.ranks': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
        'apps.referral': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
        'apps.incomes': {'handlers': ['console', 'file'], 'level': 'INFO', 'propagate': False},
    },
}
