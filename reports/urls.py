from django.conf.urls import url, patterns
from . import views

app_name = 'reports'

urlpatterns = [
    url(r'^$', views.report_list, name='report_index'),
    url(r'^new/$', views.add_or_edit, name='report_add'),
    url(r'^(?P<report_id>\d+)/$', views.show_report, name='report_detail'),
    url(r'^(?P<report_id>\d+)/(?P<page>page\d+)/$', views.show_report, name='show_report'),
    url(r'^(?P<report_id>\d+)/edit/$', views.add_or_edit, name='report_edit'),
    url(r'^(?P<report_id>\d+)/delete/$', views.delete, name='report_delete'),
    url(r'^(?P<report_id>\d+)/(?P<download>download)/$', views.show_report, name='report_download'),
]
