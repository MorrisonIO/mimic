# Django settings for mimicprint project. These are *production*
# values.

from helpers.managers import Managers

OFFLINE = False # Set to true to take entire site down and display maintenance message

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Mimic Admin', 'admin@mimicprint.com'),
    ('rGenta', 'support@rgenta.com')
)

MANAGERS = Managers('Notified by email')
#MANAGERS = (
    #('Mimic Admin', 'admin@mimicprint.com'),
    #('Laura Ambrozic', 'laura.ambrozic@mimicprint.com'),
    #('Romana Mirza', 'romana.mirza@mimicprint.com'),
    #('Shelby Flores', 'shelby.flores@mimicprint.com'),
    #('Jennifer', 'jennifer@mimicprint.com'),
    #('Rafael', 'rafael@mimicprint.com'),
    #('Production', 'production@mimicprint.com'),
#)

DATABASE_ENGINE = 'mysql'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'ado_mssql'.
DATABASE_NAME = 'mimic_oos'       # Or path to database file if using sqlite3.
DATABASE_USER = 'django_user'     # Not used with sqlite3.
DATABASE_PASSWORD = 'lrn.550$'        # Not used with sqlite3.
DATABASE_HOST = ''                # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             	# Set to empty string for default. Not used with sqlite3.

ROOT_URLCONF = 'mimicprint.urls'

# URL that handles the media served from MEDIA_ROOT.
# Example: "http://media.lawrence.com"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/admin/'

CACHE_BACKEND = 'memcached://localhost:11211/'
CACHE_MIDDLEWARE_SECONDS = 300 # 5 minutes
CACHE_MIDDLEWARE_KEY_PREFIX = ''
CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True # only cache anonymous pages, not logged in ones
