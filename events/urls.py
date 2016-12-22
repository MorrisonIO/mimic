from django.conf.urls import url, patterns
from .models import Entry

entry_info = {
    "queryset": Entry.objects.public()
}

urlpatterns = patterns('events.views', 
    url(r'^$', 
        view = 'client_events_index',
        name = 'client_events_index',
    ),        
    url(r'^search/', 
        view = 'search',
        name = 'entry_search',
    ),
    url(r'^(?P<slug>[-\w]+)/$', 
        view = 'client_events_detail',
        name = 'client_events_detail',
    ),        
)
