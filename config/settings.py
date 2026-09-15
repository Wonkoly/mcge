"""
Configuración de Django para MCG (MaestriaGeofisica).

Ver el plan de migración en /home/cokie/.claude/plans/kind-napping-grove.md
para el contexto completo de las decisiones tomadas aquí.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Carpeta escribible: base de datos, respaldos, plantillas personalizadas.
# En desarrollo coincide con el repo; en el host real puede apuntar a otra
# ruta vía la variable de entorno MCG_DATA_DIR (p. ej. una carpeta compartida
# solo para respaldos, nunca para la base de datos misma).
DATA_DIR = Path(os.environ.get("MCG_DATA_DIR", BASE_DIR / "data"))

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "django-insecure-c3qw@h0l6p0p5%4aj*d2wu#xy%rc6rd#f(^=h4aed2@1z_+yj*",
)

DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
    "accounts",
    "alumnos",
    "profesores",
    "aspirantes",
    "actas",
    "documentos",
    "dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.FlaskCompatMiddleware",
    # Login obligatorio en toda la app salvo vistas marcadas con
    # @login_not_required (solo la vista de login la usa).
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        # Motor de la app: busca en templates/ (compartido) y en el
        # subdirectorio "jinja2/" de cada app instalada (convención de
        # Django para no chocar con el backend DjangoTemplates de abajo,
        # que usa "templates/" — el que necesita el admin).
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "core.jinja2_env.environment",
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "core.context_processors.jinja_helpers",
            ],
        },
    },
    {
        # Solo para django.contrib.admin (sus plantillas son DTL, no Jinja2).
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


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": DATA_DIR / "maestria.db",
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-mx"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "dashboard:inicio"
LOGOUT_REDIRECT_URL = "accounts:login"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
