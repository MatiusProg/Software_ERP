"""
Django settings for the ERP backend.

Config se lee de variables de entorno (.env) para no filtrar secretos ni
credenciales al repo. Ver .env.example.
"""

from pathlib import Path
import os

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# Carga el .env que está junto a manage.py (backend/.env)
load_dotenv(BASE_DIR / ".env")


def env_bool(key, default=False):
    return os.getenv(key, str(default)).lower() in ("1", "true", "yes", "on")


# ----------------------------------------------------------------------------
# Seguridad
# ----------------------------------------------------------------------------
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    "django-insecure-y_vd2p66x1i!aqg9wbp#12ry408bq$0zmw6w7qyu@)j0_dd=ud",
)
DEBUG = env_bool("DJANGO_DEBUG", True)
ALLOWED_HOSTS = [h.strip() for h in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h.strip()]

# Railway publica el dominio de la app en esta variable; se añade sola para no
# tener que copiarla a mano en cada despliegue.
_dominio_railway = os.getenv("RAILWAY_PUBLIC_DOMAIN", "").strip()
if _dominio_railway and _dominio_railway not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(_dominio_railway)

# Django 4+ exige el esquema en los orígenes de confianza para POST/CSRF.
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if o.strip()
]
if _dominio_railway:
    CSRF_TRUSTED_ORIGINS.append(f"https://{_dominio_railway}")


# ----------------------------------------------------------------------------
# Apps
# ----------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Terceros
    "rest_framework",
    "django_filters",
    "corsheaders",
    # Propias
    "apps.comun",
    "apps.cuentas",
    "apps.auditoria",
    "apps.catalogo",
    "apps.terceros",
    "apps.ventas",
    "apps.tienda",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # Resuelve la organización activa del request y la deja en un thread-local
    # para el scoping multi-tenant. Debe ir DESPUÉS de AuthenticationMiddleware.
    "apps.comun.middleware.CurrentOrganizationMiddleware",
]

# WhiteNoise sirve los estáticos del admin en producción (sin nginx). En
# desarrollo estorba: avisaría de que falta la carpeta de collectstatic, que ahí
# la sirve el propio Django.
if not DEBUG:
    MIDDLEWARE.insert(2, "whitenoise.middleware.WhiteNoiseMiddleware")

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# ----------------------------------------------------------------------------
# Base de datos
#
# En desarrollo: PostgreSQL local con los DB_* del .env.
# En producción (Supabase / Railway): basta con DATABASE_URL, que es lo que
# ambos servicios entregan. Si está definida, gana sobre los DB_*.
# ----------------------------------------------------------------------------
import dj_database_url  # noqa: E402

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=600,           # reutiliza conexiones entre peticiones
            ssl_require=env_bool("DB_SSL_REQUIRE", True),
        )
    }

    # El pooler de Supabase (puerto 6543) es PgBouncer en modo transacción: cada
    # transacción puede caer en una conexión distinta, así que no sobreviven ni
    # las sentencias preparadas (psycopg3 las crea solo tras repetir una consulta)
    # ni los cursores del lado del servidor. Sin esto el despliegue arranca bien
    # y falla más tarde, cuando una consulta ya se repitió lo suficiente.
    _usa_pooler = ":6543" in DATABASE_URL or env_bool("DB_POOLER", False)
    if _usa_pooler:
        DATABASES["default"].setdefault("OPTIONS", {})["prepare_threshold"] = None
        DISABLE_SERVER_SIDE_CURSORS = True
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "erp_dev"),
            "USER": os.getenv("DB_USER", "postgres"),
            "PASSWORD": os.getenv("DB_PASSWORD", ""),
            "HOST": os.getenv("DB_HOST", "127.0.0.1"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }


# ----------------------------------------------------------------------------
# Auth
# ----------------------------------------------------------------------------
AUTH_USER_MODEL = "cuentas.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# ----------------------------------------------------------------------------
# DRF + JWT
# ----------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "apps.comun.authentication.TenantJWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_FILTER_BACKENDS": (
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ),
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 25,
}

from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
}


# ----------------------------------------------------------------------------
# CORS — la PWA (frontend) consumirá esta API desde otro origen
# ----------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:5500,http://127.0.0.1:5500,http://localhost:5173,http://127.0.0.1:5173").split(",") if o.strip()
]


# ----------------------------------------------------------------------------
# Nota de venta pública (QR)
# ----------------------------------------------------------------------------
# Dominio con el que se arman los links del QR. Vacío = se usa el host del
# request (suficiente en desarrollo y cuando la API sirve también las notas).
NOTA_PUBLICA_BASE_URL = os.getenv("NOTA_PUBLICA_BASE_URL", "").strip()


# ----------------------------------------------------------------------------
# i18n / zona horaria
# ----------------------------------------------------------------------------
LANGUAGE_CODE = "es"
TIME_ZONE = os.getenv("DJANGO_TIME_ZONE", "America/La_Paz")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"          # destino de collectstatic
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ----------------------------------------------------------------------------
# Endurecimiento para producción
#
# Solo se activa con DJANGO_DEBUG=False, para no estorbar en desarrollo (donde
# no hay HTTPS y redirigir rompería el servidor local).
# ----------------------------------------------------------------------------
if not DEBUG:
    # Railway/Supabase terminan el TLS antes de Django: sin esto, Django cree
    # que la petición es HTTP y entra en un bucle de redirecciones.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", True)
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = "DENY"
