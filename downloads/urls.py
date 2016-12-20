from django.conf.urls import url, patterns
from .models import Download

info_dict = {
    'queryset': Download.objects.all(),
}

urlpatterns = patterns('mimicprint.downloads.views',
    url(r'^$', 
        view = 'index',
        name = 'download_index',
    ),
    url(r'^(?P<download_id>\d+)/$', 
        view = 'detail',
        name = 'download_detail',
    ),
    url(r'^(?P<download_id>\d+)/delete/$', 
        view = 'delete',
        name = 'download_delete'
    ),
    url(r'^(?P<download_id>\d+)/undo_delete/$', 
        view = 'undo_delete',
        name = 'download_undo_delete'
    ),
)
