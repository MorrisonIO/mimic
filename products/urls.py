from django.conf.urls import url, patterns
from . import views

app_name = 'products'

urlpatterns = [
    url(r'^$',  views.index, name = 'product_list'),
    url(r'^search/$', views.search, name = 'product_search'),
    url(r'^create_pdf/$', views.create_pdf, name='create_pdf'),
]
