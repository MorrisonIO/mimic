from django.conf.urls import url, patterns
from .models import Address

urlpatterns = patterns('addresses.views',
    url(r'^$',
        view = 'index',
        name = 'address_index',
    ),
    url(r'^search/',
        view = 'search',
        name = 'address_search',
    ),
    url(r'^add/$',
        view = 'add_or_edit',
        name = 'address_add'
    ),
    url(r'^(?P<address_id>\d+)/$',
        view = 'detail',
        name = 'address_detail',
    ),
    url(r'^(?P<address_id>\d+)/delete/$',
        view = 'delete',
        name = 'address_delete'
    ),
    url(r'^undo_delete/(?P<token>.+)/$',
        view = 'undo_delete',
        name = 'address_undo_delete'
    ),
    url(r'^(?P<address_id>\d+)/edit/$',
        view = 'add_or_edit',
        name = 'address_edit'
    ),
    url(r'^(?P<address_id>\d+)/(?P<duplicate>duplicate)/$',
        view = 'add_or_edit',
        name = 'address_duplicate'
    ),
)
