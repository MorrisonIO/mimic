from django.conf.urls import url, patterns
from . import views

app_name = 'addresses'

urlpatterns = [
    url(r'^$', views.index, name='address_index'),
    url(r'^search/$', views.search, name='address_search'),
    url(r'^add/$', views.add_or_edit, name='address_add'),
    url(r'^(?P<address_id>\d+)/$', views.detail, name='address_detail'),
    url(r'^(?P<address_id>\d+)/delete/$', views.delete, name='address_delete'),
    url(r'^undo_delete/(?P<token>.+)/$', views.undo_delete, name='address_undo_delete'),
    url(r'^(?P<address_id>\d+)/edit/$', views.add_or_edit, name='address_edit'),
    url(r'^(?P<address_id>\d+)/(?P<duplicate>duplicate)/$', views.add_or_edit, name='address_duplicate'),
]