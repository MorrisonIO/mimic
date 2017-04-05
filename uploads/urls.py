from django.conf.urls import url, patterns
from django.views.generic import TemplateView
from . import views

app_name = "uploads"

urlpatterns = [
    url(r'^$', views.upload_file, name='upload_file'),
    url(r'^progress/$', views.upload_progress),
    url(r'^ok/$', TemplateView.as_view(template_name='uploads/ok.html'), name='upload_ok'),
    url(r'^list/$', views.show_list, name='upload_list'),
]
