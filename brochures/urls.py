from django.conf.urls import url, patterns
from . import views

app_name = 'brochures'

urlpatterns = [
    url(r'^$', views.index, name='brochures'),
    url(r'^create_pdf/(?P<template_id>.*)/$', views.create_pdf, name='create_pdf'),
    url(r'^view/(?P<template_id>.*)/$', views.render_view, name='render_including_template'),
    url(r'^get_brochure_modal_data/$', views.get_brochure_modal_data, name='create_brochure_modal'),

    url(r'^personal$', views.personal_info, name='personal_info'),
    url(r'^property/$', views.property_info, name='property_info'),
    url(r'^detail/$', views.detail_page, name='detail'),
    url(r'^preview/$', views.preview_page, name='preview'),
    url(r'^shipping/$', views.ship_and_mail, name='ship_and_mail'),
]
