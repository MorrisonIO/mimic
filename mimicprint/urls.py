"""mimicprint URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Add an import:  from blog import urls as blog_urls
    2. Import the include() function: from django.conf.urls import url, include
    3. Add a URL to urlpatterns:  url(r'^blog/', include(blog_urls))
"""
from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from contact_form.views import ContactFormView
from .forms import FeedbackForm
from . import views
from orders import admin_views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^page/', views.page),
    # Authentication
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    url(r'^accounts/logout/$', 'mimicprint.views.logout_user', name='logout'),
    url(r'^accounts/profile/$', views.profile, name='profile'),
    # url(r'^accounts/password_change/$',
    #     view = 'django.contrib.auth.views.password_change',
    #     name = 'password_change'
    # ),
    # url(r'^accounts/password_change/done/$', 'django.contrib.auth.views.password_change_done'),
    # url(r'^accounts/password_reset/$',
    #     'django.contrib.auth.views.password_reset',
    #     name = 'password_reset'
    # ),
    # url(r'^accounts/password_reset/done/$', 'django.contrib.auth.views.password_reset_done'),
    # url(r'^accounts/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),

    url(r'^oos/$',
        views.dashboard,
        name='dashboard',
    ),
    url(r'^oos/setorg/$',
        views.setorg,
        name='setorg',
    ),
    url(r'^oos/addresses/', include('addresses.urls')),
    url(r'^oos/products/', include('products.urls')),
    url(r'^oos/brochures/', include('brochures.urls')),
    url(r'^oos/orders/', include('orders.urls')),
    url(r'^oos/vardata/', include('vardata.urls')),
    url(r'^oos/reports/', include('reports.urls')),
    url(r'^oos/charts/', include('charts.urls')),
    url(r'^oos/downloads/', include('downloads.urls')),
    url(r'^oos/events/', include('events.urls')),
    url(r'^upload/', include('uploads.urls')),

    # Admin
    url(r'^admin/orders/fastorder/add/$', admin_views.fastorder_add),
    url(r'^admin/orders/products_ordered/(?P<order_id>\d+)/$', admin_views.products_ordered),
    url(r'^admin/orders/worknote_view/(?P<worknote_id>\d+)/$', admin_views.worknote_view),
    url(r'^admin/orders/dockets/(?P<order_id>\d+)/$', admin_views.create_docket),
    url(r'^admin/orders/save_invnum/$', admin_views.save_invnum, name=''),
    url(r'^admin/orders/shipping/packing_slip/(?P<order_id>\d+)/$', admin_views.create_packingslip),
    url(r'^admin/orders/shipping/label/(?P<order_id>\d+)/$', admin_views.create_label),
    url(r'^admin/orders/shipping/comm_inv/(?P<order_id>\d+)/$', admin_views.create_comm_inv),

    url(r'^oos/feedback/$', ContactFormView.as_view(form_class=FeedbackForm),
        # {
        #     'form_class': FeedbackForm,
        #     'success_url': '/oos/feedback/sent/',
        # },
        name='contact_form'),
    url(r'^oos/feedback/sent/$',
        TemplateView.as_view(template_name='contact_form/contact_form_sent.html'),
        name='contact_form_sent'),

] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) 

if settings.DEBUG is True:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
