# /srv/nfse/repo/emissor_gold/settings_prod.py
from .settings import *  # noqa
import os

DEBUG = False
SECRET_KEY = os.getenv("SECRET_KEY")  # vem do .env.prod
ALLOWED_HOSTS = ["nfse.taxgold.com.br"]
CSRF_TRUSTED_ORIGINS = ["https://nfse.taxgold.com.br"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "nfse_prod",
        "USER": "nfse_owner",
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": "127.0.0.1",
        "PORT": "5432",
    }
}

# Sirva estáticos e mídia fora do repo
STATIC_URL = "/static/"
STATIC_ROOT = "/srv/nfse/staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = "/srv/nfse/media"

# HTTPS atrás do Nginx
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Hardening (ative assim que tudo ok)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Configurações de Sessão - Logout automático após inatividade
SESSION_COOKIE_AGE = 900  # 15 minutos (900 segundos)
SESSION_SAVE_EVERY_REQUEST = True  # Renova a sessão a cada requisição
SESSION_EXPIRE_AT_BROWSER_CLOSE = True  # Expira ao fechar o navegador
SESSION_COOKIE_HTTPONLY = True  # Proteção contra XSS
SESSION_COOKIE_SAMESITE = 'Lax'  # Proteção contra CSRF
