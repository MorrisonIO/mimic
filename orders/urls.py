from django.conf.urls.defaults import *

urlpatterns = patterns('mimicprint.orders.views',
    url(r'^$', 
        view = 'order_list',
        name = 'order_index',
    ),
    url(r'^search/', 
        view = 'search',
        name = 'order_search',
    ),
    url(r'^(?P<order_id>\d+)/$', 
        'show_order',
        {'confirm': False},
        name = 'order_detail',
    ),
    url(r'^(?P<order_id>\d+)/confirmed/$', 
        'show_order',
        {'confirm': True},
        name = 'order_confirmation',
    ),
    url(r'^approve/$', 
        view = 'approve_order',
        name = 'approve_order',
    ),
    url(r'^your_order/(?P<unique_id>\d+)/input/$', 
        view = 'vardata_remodify',
        name = 'vardata_remodify',
    ),
    url(r'^your_order/input/$', 
        view = 'vardata_input',
        name = 'vardata_input',
    ),
    url(r'^your_order/preview/$',
        view = 'vardata_preview',
        name = 'vardata_preview',
    ),
    url(r'^process_products/$', 
        view = 'process_products',
        name = 'process_products',
    ),
    url(r'^your_order/$', 
        view = 'cart_summary',
        name = 'cart_summary',
    ),
    url(r'^your_order/cancel/$', 
        view = 'cancel_order',
        name = 'cancel_order',
    ),
    url(r'^(?P<unique_id>\d+)/delete/$', 
        view = 'delete_from_cart',
        name = 'delete_item',
    ),
    url(r'^your_order/shipping/$', 
        view = 'provide_shipto',
        name = 'provide_shipto',
    ),
    url(r'^your_order/additional/$', 
        view = 'provide_addinfo',
        name = 'provide_addinfo',
    ),
    url(r'^your_order/confirm/$', 
        view = 'confirm_order',
        name = 'confirm_order',
    ),
    url(r'^your_order/submitted/$', 
        view = 'process_order',
        name = 'process_order',
    ),
)
