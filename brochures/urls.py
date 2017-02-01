from django.conf.urls import url, patterns
from . import views

app_name = 'brochures'

urlpatterns = [
    url(r'^$', views.index, name='brochures'),
    url(r'^create_pdf/(?P<template_name>.*)/$', views.create_pdf, name='create_pdf'),
    url(r'^view/(?P<template_name>.*)/$', views.render_view, name='render_including_template'),
    url(r'^get_menu_data/$', views.create_menu_elems, name='create_menu'),
]
