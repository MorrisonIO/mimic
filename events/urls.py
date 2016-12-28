from django.conf.urls import url, patterns
from .models import Entry
from . import views

entry_info = {
    "queryset": Entry.objects.public()
}

app_name = 'events'

urlpatterns = [
    url(r'^$', views.client_events_index, name='client_events_index'),
    url(r'^search/', views.search, name='entry_search'),
    url(r'^(?P<slug>[-\w]+)/$', views.client_events_detail, name='client_events_detail'),
]
