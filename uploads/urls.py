from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

urlpatterns = patterns('mimicprint.uploads.views',
    url(r'^$', 
        view = 'upload_file',
        name = 'upload_file',
    ),
    (r'^progress/$', 'upload_progress'),
    url(r'^ok/$', 
        direct_to_template, {'template': 'uploads/ok.html'},
        name = 'upload_ok',
    ),
)
