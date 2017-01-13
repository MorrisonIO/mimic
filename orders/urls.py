from django.conf.urls import url
from . import views

app_name = 'orders'

urlpatterns = [
    url(r'^$', views.order_list, name='order_index'),
    url(r'^search/', views.search, name='order_search'),
    url(r'^(?P<order_id>\d+)/$', views.show_order, {'confirm': False}, name='order_detail'),
    url(r'^(?P<order_id>\d+)/confirmed/$', views.show_order, {'confirm': True}, name='order_confirmation'),
    url(r'^approve/$', views.approve_order, name='approve_order'),
    url(r'^your_order/(?P<unique_id>\d+)/input/$', views.vardata_remodify, name='vardata_remodify'),
    url(r'^your_order/input/$', views.vardata_input, name='vardata_input'),
    url(r'^your_order/preview/$', views.vardata_preview, name='vardata_preview'),
    url(r'^process_products/$', views.process_products, name='process_products'),
    url(r'^your_order/$', views.cart_summary, name='cart_summary'),
    url(r'^your_order/cancel/$', views.cancel_order, name='cancel_order'),
    url(r'^(?P<unique_id>\d+)/delete/$', views.delete_from_cart, name='delete_item'),
    url(r'^your_order/shipping/$', views.provide_shipto, name='provide_shipto'),
    url(r'^your_order/additional/$', views.provide_addinfo, name='provide_addinfo'),
    url(r'^your_order/confirm/$', views.confirm_order, name='confirm_order'),
    url(r'^your_order/submitted/$', views.process_order, name='process_order'),
]
