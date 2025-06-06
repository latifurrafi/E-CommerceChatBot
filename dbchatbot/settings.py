import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-replace-with-your-own-key'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []

# Application definition
INSTALLED_APPS = [
    'unfold',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'chatapp',  # Add our chat application
    'ecommerce',  # E-commerce application
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'dbchatbot.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'dbchatbot.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

# Media files (User uploaded content)
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Embedding directory
EMBEDDING_DIR = os.path.join(BASE_DIR, 'embeddings')

UNFOLD = {
    'ADMIN_FAVICON': 'path/to/favicon.ico',  # Optional
    'ADMIN_TITLE': 'Your Admin Title',
    'MENU': [
        {'label': 'Dashboard', 'url': 'admin:index'},
        {'label': 'Products', 'url': 'admin:chatapp_product_changelist'},
        {'label': 'FAQs', 'url': 'admin:chatapp_faq_changelist'},
        {'label': 'Orders', 'url': 'admin:chatapp_order_changelist'},
        {'label': 'Order Items', 'url': 'admin:chatapp_orderitem_changelist'},
        {'label': 'Embeddings', 'url': 'admin:chatapp_embedding_changelist'},
        # E-commerce menu items
        {'label': 'E-commerce', 'items': [
            {'label': 'Categories', 'url': 'admin:ecommerce_category_changelist'},
            {'label': 'Products', 'url': 'admin:ecommerce_product_changelist'},
            {'label': 'Variations', 'url': 'admin:ecommerce_variation_changelist'},
            {'label': 'Carts', 'url': 'admin:ecommerce_cart_changelist'},
            {'label': 'Orders', 'url': 'admin:ecommerce_order_changelist'},
        ]},
    ],
}