"""
Django settings for Product_Screen_Server project.

Этот файл содержит основные настройки проекта, включая:
- конфигурацию приложений
- параметры базы данных
- настройки middleware и шаблонов
- настройки каналов и WebSocket (через Django Channels)
- подключение Redis для кэширования и каналов
"""


import os

from pathlib import Path
from decouple import config

# Базовая директория проекта (на уровень выше текущего файла)
BASE_DIR = Path(__file__).resolve().parent.parent

# Секретный ключ для Django, считывается из .env
SECRET_KEY = config('DJANGO_SECRET_KEY')

# Включение режима отладки (True — для разработки)
DEBUG = True

# Разрешённые хосты, с которых можно обращаться к приложению
ALLOWED_HOSTS = ['localhost', '127.0.0.1']


# Установленные приложения проекта
INSTALLED_APPS = [
    'channels',
    'daphne',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'Screen_Server.apps.ScreenServerConfig',
]

# Путь к ASGI-приложению для запуска Channels
ASGI_APPLICATION = 'Product_Screen_Server.asgi.application'

# Настройка слоя каналов через Redis (для обмена сообщениями)
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('localhost', 6379)],
        }
    }
}

# Middleware-цепочка — обработчики запросов/ответов
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Основной конфиг для URL-роутинга
ROOT_URLCONF = 'Product_Screen_Server.urls'

# Настройки шаблонов (template engine)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

# WSGI_APPLICATION = 'Product_Screen_Server.wsgi.application'

# Подключение базы данных (SQLite по умолчанию)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Валидаторы пароля
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Язык и часовой пояс
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Настройки статики
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static'
STATICFILES_DIRS = [
    BASE_DIR / 'Screen_Server/static',
]

# Настройки медиа-файлов (загрузка изображений и прочего)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Автоматическая генерация ID для моделей
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Настройка кэша через Redis
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
