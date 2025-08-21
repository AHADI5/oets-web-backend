# oets/settings.py
# Django settings for oets project.
# This file contains the settings for the Online Education and Training System (OETS).
# It includes configurations for database, authentication, static files, and more.

# Note: Ensure you have the necessary environment variables set in a .env file or your deployment environment.
# import necessary modules
import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# Load environment variables from .env file
# Ensure you have a .env file with the necessary variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent# Base directory of the project

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')# Ensure this is set in your .env file

DEBUG = os.getenv('DEBUG', 'True') == 'True'# Set to False in production

ALLOWED_HOSTS = ['*']  # Update for production

INSTALLED_APPS = [
    'django.contrib.admin',# Admin interface
    'django.contrib.auth',# Authentication framework
    'django.contrib.contenttypes',# Content types framework
    'django.contrib.sessions',# Session management
    'django.contrib.messages',# Message framework
    'django.contrib.staticfiles',# Static files management
    'rest_framework',# Django REST Framework for API development
    'rest_framework.authtoken',# For token-based authentication
    'core',# Core application for user management and courses
    'django_filters',  # For advanced filtering capabilities
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

ROOT_URLCONF = 'oets.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR,'templates'),
        ],
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

WSGI_APPLICATION = 'oets.wsgi.application'

# Database Configuration
# ----------------------
# This configuration provides flexible database setup with the following priority:
# 1. First tries to use DATABASE_URL if it exists (recommended for production)
# 2. Falls back to individual DB_* environment variables if they exist
# 3. Defaults to SQLite if no other configuration is provided (good for development)
DATABASES = {
    'default': 
        # Option 1: Use DATABASE_URL if available (most deployment platforms provide this)
        dj_database_url.parse(
            os.getenv('DATABASE_URL'),
            conn_max_age=600,           # Persistent database connections
            conn_health_checks=True,    # Enable connection health checks
        ) if os.getenv('DATABASE_URL') else
        
        # Option 2: Use individual PostgreSQL variables if any are set
        {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('DB_NAME', 'oets_db'),          # Database name
            'USER': os.getenv('DB_USER', 'oets_user'),        # Database user
            'PASSWORD': os.getenv('DB_PASSWORD', 'oets_password'),  # Database password
            'HOST': os.getenv('DB_HOST', 'localhost'),        # Database host
            'PORT': os.getenv('DB_PORT', '5432'),             # Database port
        } if any(os.getenv(var) for var in ['DB_NAME', 'DB_USER', 'DB_PASSWORD', 'DB_HOST', 'DB_PORT']) else
        
        # Option 3: Default to SQLite (for development when no other config exists)
        {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),  # Database file location
        }
}
# Custom User Model
# -------------------   
# Point to the custom user model defined in core/models.py
# This allows for extending the default user model with additional fields.
AUTH_USER_MODEL = 'core.User'  # Point to your custom user model

AUTH_PASSWORD_VALIDATORS = [
    # Validator 1: Checks if password is too similar to user attributes
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        # Options (default values shown):
        # 'OPTIONS': {
        #     'max_similarity': 0.7,  # Threshold for similarity (0-1)
        #     'user_attributes': ('username', 'first_name', 'last_name', 'email')
        # }
    },
    
    # Validator 2: Enforces minimum password length
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,  # Minimum password length requirement
            # Note: NIST recommends at least 8 characters
            # For higher security, consider increasing to 12+
        }
    },
    
    # Validator 3: Prevents common/popular passwords
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        # Checks against a list of 20,000 common passwords
        # No configurable options
    },
    
    # Validator 4: Prevents entirely numeric passwords
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        # Rejects passwords containing only numbers
        # Particularly important as many users default to numeric PINs
    },
    
    # Additional validators you might consider adding:
    {
        'NAME': 'django.contrib.auth.password_validation.UppercaseValidator',
        'OPTIONS': {
            'min_uppercase': 1  # Require at least 1 uppercase letter
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.SymbolValidator',
        'OPTIONS': {
            'min_symbols': 1  # Require at least 1 special character
        }
    }
]

# Internationalization
# -------------------
# Language code for translations (English - United States)
LANGUAGE_CODE = 'en-us'

# Timezone settings (UTC+2 for Goma, DR Congo)
# Note: Africa/Lubumbashi is the closest official timezone to Goma
TIME_ZONE = 'Africa/Lubumbashi'  # UTC+2
USE_I18N = True    # Enable internationalization
USE_L10N = True    # Enable localization
USE_TZ = True      # Enable timezone awareness

# Static files (CSS, JavaScript, Images)
# -------------------------------------
STATIC_URL = 'static/'  # URL prefix for static files
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')  # Collected static files dir

# Media files (User-uploaded content)
# ----------------------------------
MEDIA_URL = 'media/'  # URL prefix for media files
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')  # Local filesystem path for media

# Default primary key field type
# -----------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Django REST Framework Settings
# ----------------------------
# Django REST Framework Settings
# ----------------------------
REST_FRAMEWORK = {
    # Authentication classes
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
    
    # Default permission classes
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    
    # Filter backends configuration
    'DEFAULT_FILTER_BACKENDS': [
        # 1. DjangoFilterBackend - for field-level filtering
        'django_filters.rest_framework.DjangoFilterBackend',
        
        # 2. SearchFilter - for full-text search across multiple fields
        'rest_framework.filters.SearchFilter',
        
        # 3. OrderingFilter - for dynamic field ordering
        'rest_framework.filters.OrderingFilter',
    ],
    
    # Optional: Default filter settings
    'DEFAULT_FILTER_BACKENDS': {
        'django_filters.rest_framework.DjangoFilterBackend': {
            'filter_fields': '__all__',  # Default fields to allow filtering on
        },
        'rest_framework.filters.SearchFilter': {
            'search_param': 'search',  # URL query parameter for search
        },
        'rest_framework.filters.OrderingFilter': {
            'ordering_param': 'ordering',  # URL query parameter for ordering
        },
    }
}

# Security Settings (Production Only)
# ----------------------------------
if not DEBUG:
    # HTTPS Settings
    SECURE_SSL_REDIRECT = True       # Redirect all HTTP to HTTPS
    SESSION_COOKIE_SECURE = True     # Only send session cookie over HTTPS
    CSRF_COOKIE_SECURE = True        # Only send CSRF cookie over HTTPS
    
    # HTTP Strict Transport Security
    SECURE_HSTS_SECONDS = 31536000   # 1 year HSTS policy
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True  # Include all subdomains
    SECURE_HSTS_PRELOAD = True       # Preload HSTS policy
    
    # Additional recommended security settings:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    
    # For production deployments with load balancers:
    # SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')