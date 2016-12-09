# Django settings for mimicprint project.

import os

PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))

# Local time zone for this installation. Choices can be found here:
# http://www.postgresql.org/docs/8.1/static/datetime-keywords.html#DATETIME-TIMEZONE-SET-TABLE
# although not all variations may be possible on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Canada/Eastern'

# Language code for this installation. All choices can be found here:
# http://www.w3.org/TR/REC-html40/struct/dirlang.html#langcodes
# http://blogs.law.harvard.edu/tech/stories/storyReader$15
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = False

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'f7eb1rvri=&xp_-mum-vm_@h%c-53jc-2lro6=waw1_=@j(o&s'

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')

# Directory where the custom font files are located, for variable documents
FONT_DIR = os.path.join(PROJECT_PATH, 'fonts')

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_PATH, 'templates'),
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.cache.UpdateCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.doc.XViewMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',
    'django.contrib.flatpages.middleware.FlatpageFallbackMiddleware',
#    'debug_toolbar.middleware.DebugToolbarMiddleware',
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.markup',
    'django.contrib.flatpages',
#    'debug_toolbar',
    'contact_form',
    'mimicprint.helpers',
    'mimicprint.addresses',
    'mimicprint.products',
    'mimicprint.orgs',
    'mimicprint.orders',
    'mimicprint.vardata',
    'mimicprint.reports',
    'mimicprint.downloads',
    'mimicprint.events',
)

# Template context processors. A tuple of callables that are used to
# populate the context in RequestContext.
TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.request",
    "mimicprint.inject_org.inject"
)

AUTH_PROFILE_MODULE = 'orgs.UserProfile'

# Authentication
LOGIN_URL = '/accounts/login/'
LOGOUT_URL = '/accounts/logout/'
LOGIN_REDIRECT_URL = '/oos/setorg/'

# Session length. Set to true to have session cookies expire when user
# closes browser. If false, cookies are stored for SESSION_COOKIE_AGE
# (default 2 weeks).
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# EMAIL SETTINGS
# The e-mail address that error messages come from, such as those sent
# to ADMINS and MANAGERS.
SERVER_EMAIL = 'Mimic Admin <admin@mimicprint.com>'

# Default e-mail address to use for various automated correspondence from the site manager(s).
DEFAULT_FROM_EMAIL = 'Mimic Print & Media Services <support@mimicprint.com>'

# Email account details
EMAIL_HOST          = 'mail.mimicprint.com'
EMAIL_PORT          = '25'
EMAIL_HOST_USER     = ''
EMAIL_HOST_PASSWORD = ''

# This is prepended to the subject of messages sent with mail_managers
# and mail_admins. Defaults to [Django]
EMAIL_SUBJECT_PREFIX = '[Mimic OOS] '

from django.conf import global_settings
FILE_UPLOAD_HANDLERS = ('mimicprint.uploads.upload_handler.UploadProgressCachedHandler', ) + global_settings.FILE_UPLOAD_HANDLERS

# import local settings overriding the defaults
try:
    from settings_local import *
except ImportError:
    try:
        from mod_python import apache
        apache.log_error( "local settings not available", apache.APLOG_NOTICE )
    except ImportError:
        import sys
        sys.stderr.write( "local settings not available\n" )
