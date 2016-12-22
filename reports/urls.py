from django.conf.urls import url, patterns

urlpatterns = patterns('reports.views',
    url(r'^$', 
        view = 'report_list',
        name = 'report_index',
    ),
    url(r'^new/$', 
        view = 'add_or_edit',
        name = 'report_add',
    ),
    url(r'^(?P<report_id>\d+)/$', 
        view = 'show_report',
        name = 'report_detail',
    ),
    url(r'^(?P<report_id>\d+)/(?P<page>page\d+)/$', 
        view = 'show_report',
        name = 'show_report'
    ),
    url(r'^(?P<report_id>\d+)/edit/$', 
        view = 'add_or_edit',
        name = 'report_edit'
    ),
    url(r'^(?P<report_id>\d+)/delete/$', 
        view = 'delete',
        name = 'report_delete'
    ),
    url(r'^(?P<report_id>\d+)/(?P<download>download)/$', 
        view = 'show_report',
        name = 'report_download'
    ),
)
