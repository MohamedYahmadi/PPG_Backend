from .base import *
from dotenv import load_dotenv
import sys
import os
# Charge le fichier .env
load_dotenv(BASE_DIR / '.env')
# Configuration GDAL (Nécessaire pour GeoDjango sur Windows)
def find_gdal():
    # 1. Check environment variables first
    env_bin = os.environ.get('GDAL_BIN_PATH')
    env_dll = os.environ.get('GDAL_DLL_NAME', 'gdal312.dll')
    if env_bin and os.path.exists(os.path.join(env_bin, env_dll)):
        return env_bin, env_dll

    # 2. Check common installation paths
    common_paths = [
        r'C:\OSGeo4W\bin',
        r'C:\Users\Mohamed_Yahmadi\AppData\Local\Programs\OSGeo4W\bin', # Votre chemin actuel
        r'C:\Program Files\OSGeo4W\bin',
        r'C:\OSGeo4W64\bin',
    ]
    common_dlls = ['gdal312.dll', 'gdal311.dll', 'gdal310.dll', 'gdal309.dll', 'gdal308.dll', 'gdal307.dll']
    
    for path in common_paths:
        if os.path.exists(path):
            for dll in common_dlls:
                if os.path.exists(os.path.join(path, dll)):
                    return path, dll
    return None, None

GDAL_BIN_PATH, GDAL_DLL_NAME = find_gdal()

if os.name == 'nt' and GDAL_BIN_PATH: # Windows
    if GDAL_BIN_PATH not in os.environ['PATH']:
        os.environ['PATH'] = GDAL_BIN_PATH + os.pathsep + os.environ['PATH']
    GDAL_LIBRARY_PATH = os.path.join(GDAL_BIN_PATH, GDAL_DLL_NAME)

ALLOWED_HOSTS = ['*']
CORS_ALLOW_ALL_ORIGINS = True

# Overwrite DB with local settings
DATABASES['default'] = {
    'ENGINE': 'django.contrib.gis.db.backends.postgis',
    'NAME': os.environ.get('DB_NAME', 'sitp_db'),
    'USER': os.environ.get('DB_USER', 'postgres'),
    'PASSWORD': os.environ.get('DB_PASSWORD', 'postgres'),
    'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
    'PORT': os.environ.get('DB_PORT', '5432'),
}

CELERY_BROKER_URL = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/0')

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get('REDIS_WS_URL', 'redis://127.0.0.1:6379/1')],
        },
    },
}

# ==============================================================================
# OBSERVABILITY & LOGGING (Local JSON Format)
# ==============================================================================
# Sauf si on run les tests (pytest override stdout)
if 'pytest' not in sys.modules:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'json': {
                '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
                'fmt': '%(asctime)s %(levelname)s %(name)s %(message)s'
            },
            'simple': {
                'format': '[%(levelname)s] %(message)s'
            }
        },
        'handlers': {
            'console_json': {
                'class': 'logging.StreamHandler',
                'formatter': 'json',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['console_json'],
                'level': 'INFO',
                'propagate': False,
            },
            'domains': { # Nos logs métier
                'handlers': ['console_json'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
