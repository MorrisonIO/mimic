from django.conf.urls import url
from . import views

app_name = 'charts'

urlpatterns = [
    url(r'^$', views.index, name='chart_index'),
    url(r'^(?P<chart>(products|orgs|users))/$', views.make_chart, name='chart_detail'),
]