from django.conf.urls import url, patterns
from .models import Download
from . import views

info_dict = {
    'queryset': Download.objects.all(),
}

app_name = 'downloads'

urlpatterns = [
    url(r'^$', views.index, name='download_index'),
    url(r'^(?P<download_id>\d+)/$', views.detail, name='download_detail'),
    url(r'^(?P<download_id>\d+)/delete/$', views.delete, name='download_delete'),
    url(r'^(?P<download_id>\d+)/undo_delete/$', views.undo_delete, name='download_undo_delete'),
]
