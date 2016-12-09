from django.conf.urls.defaults import *

urlpatterns = patterns('mimicprint.charts.views',
    url(r'^$', 
        view = 'index',
        name = 'chart_index',
    ),
    url(r'^(?P<chart>(products|orgs|users))/$', 
        view = 'make_chart',
        name = 'chart_detail'
    ),
)
