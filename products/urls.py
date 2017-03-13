from django.conf.urls import url, patterns
from . import views

app_name = 'products'

urlpatterns = [
    url(r'^$',  views.index, name='product_list'),
    url(r'^search/$', views.search, name='product_search'),
    url(r'^category/$', views.get_category, name="get_category"),
    url(r'^get_product_modal_data/$', views.get_product_modal_data, name="get_category"),
]
