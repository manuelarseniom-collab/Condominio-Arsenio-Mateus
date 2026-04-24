import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

# MySQL: defina DJANGO_USE_MYSQL=1 e MYSQL_* (ou use SQLite local por defeito).
USE_MYSQL = os.environ.get("DJANGO_USE_MYSQL", "").lower() in ("1", "true", "yes")

SECRET_KEY = "CHANGE_ME_DJANGO_SECRET_KEY"

DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "site_publico",
    "clientes",
    "unidades",
    "faturacao",
    "reservas",
    "depoimentos",
    "limpeza",
    "lavandaria",
    "restaurante",
    "dashboard",
    "relatorios",
    "usuarios",
    "portal_cliente",
    "operacoes",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "usuarios.middleware.ClienteConfirmadoMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "condominio_web.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "condominio_web.context_processors.navigation_context",
            ],
        },
    },
]

WSGI_APPLICATION = "condominio_web.wsgi.application"
ASGI_APPLICATION = "condominio_web.asgi.application"


if USE_MYSQL:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("MYSQL_DATABASE", "condominio_web"),
            "USER": os.environ.get("MYSQL_USER", "root"),
            "PASSWORD": os.environ.get("MYSQL_PASSWORD", ""),
            "HOST": os.environ.get("MYSQL_HOST", "127.0.0.1"),
            "PORT": os.environ.get("MYSQL_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-pt"
TIME_ZONE = "Africa/Luanda"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

LOGIN_URL = "usuarios:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "site_publico:home"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Email (consola em desenvolvimento; configure SMTP em produção)
EMAIL_BACKEND = os.environ.get(
    "DJANGO_EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "noreply@arseniomateus.ao")

# Referência de pagamento (entidade fictícia até integração bancária)
PAGAMENTO_ENTIDADE_REF = os.environ.get("PAGAMENTO_ENTIDADE_REF", "12345")

# Contactos oficiais do portal (usar no footer e páginas públicas)
CONTACT_EMAIL = os.environ.get("CONTACT_EMAIL", "manuelarseniom@gmail.com")
CONTACT_PHONE = os.environ.get("CONTACT_PHONE", "+244 939 520 195")

# WhatsApp da receção (apenas dígitos, com código do país) — link em páginas e emails
RECECAO_WHATSAPP_MSISDN = os.environ.get("RECECAO_WHATSAPP_MSISDN", "244939520195")
