from django.conf.urls.defaults import *
from django.contrib import admin
from django.conf import settings
from django.views.generic.simple import direct_to_template
from django.views.generic import list_detail
from django.contrib.auth.decorators import login_required
from django.views.generic.simple import direct_to_template
from contact_form.views import contact_form
from mimicprint.forms import FeedbackForm
from mimicprint.events.models import Entry
import os
admin.autodiscover()

public_entry_dict = {
    'queryset': Entry.objects.public().order_by('-date_created'),
    'template_object_name': 'entry',
}

urlpatterns = patterns('',
    # MAIN SITE
    # Any page not listed below is handled by the flatpages framework.
    (r'^(2D7pzEn\.html)/?$', 'django.views.static.serve', {'document_root': os.path.join(settings.PROJECT_PATH, 'public')}),
    (r'^upload/', include('mimicprint.uploads.urls')),
    url(r'^news/$',
        list_detail.object_list,
        public_entry_dict,
        'public_events_index',
    ),
    url(r'^news/(?P<slug>[-\w]+)/$',
        list_detail.object_detail,
        public_entry_dict,
        'public_events_detail',
    ),
)

if settings.OFFLINE:
    urlpatterns += patterns('',
        url(r'^oos/',
            'django.views.generic.simple.direct_to_template', {'template': 'base_offline.html'},
            name = 'offline',
        ),
        url(r'^accounts/',
            'django.views.generic.simple.direct_to_template', {'template': 'base_offline.html'},
            name = 'offline',
        ),
        url(r'^admin/',
            'django.views.generic.simple.direct_to_template', {'template': 'base_offline.html'},
            name = 'offline',
        ),
    )

else:
    urlpatterns += patterns('',
        # ONLINE ORDERING SYSTEM
        # Home
        url(r'^oos/$',
            view = 'mimicprint.views.dashboard',
            name = 'dashboard',
        ),
        url(r'^oos/setorg/$',
            view = 'mimicprint.views.setorg',
            name = 'setorg',
        ),

        # Admin
        (r'^admin/orders/fastorder/add/$', 'mimicprint.orders.admin_views.fastorder_add'),
        (r'^admin/orders/products_ordered/(?P<order_id>\d+)/$', 'mimicprint.orders.admin_views.products_ordered'),
        (r'^admin/orders/worknote_view/(?P<worknote_id>\d+)/$', 'mimicprint.orders.admin_views.worknote_view'),
        (r'^admin/orders/dockets/(?P<order_id>\d+)/$', 'mimicprint.orders.admin_views.create_docket'),
        (r'^admin/orders/save_invnum/$', 'mimicprint.orders.admin_views.save_invnum'),
        (r'^admin/orders/shipping/packing_slip/(?P<order_id>\d+)/$', 'mimicprint.orders.admin_views.create_packingslip'),
        (r'^admin/orders/shipping/label/(?P<order_id>\d+)/$', 'mimicprint.orders.admin_views.create_label'),
        (r'^admin/orders/shipping/comm_inv/(?P<order_id>\d+)/$', 'mimicprint.orders.admin_views.create_comm_inv'),
        (r'^admin/products/duplicate/(?P<product_id>\d+)/$', 'mimicprint.products.admin_views.duplicate_product'),
        (r'^admin/products/export/settings$', 'mimicprint.products.admin_views.export_settings'),
        (r'^admin/products/export/download$', 'mimicprint.products.admin_views.export_products'),
        (r'^admin/(.*)', admin.site.root),
        (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', {'packages': 'django.conf'}),

        # Authentication
        url(r'^accounts/login/$',
            'django.contrib.auth.views.login',
            name = 'login'
        ),
        url(r'^accounts/logout/$',
            'mimicprint.views.logout_user',
            name = 'logout'
        ),
        url(r'^accounts/profile/$',
            view = 'mimicprint.views.profile',
            name = 'profile'
        ),
        url(r'^accounts/password_change/$',
            view = 'django.contrib.auth.views.password_change',
            name = 'password_change'
        ),
        (r'^accounts/password_change/done/$', 'django.contrib.auth.views.password_change_done'),
        url(r'^accounts/password_reset/$',
            'django.contrib.auth.views.password_reset',
            name = 'password_reset'
        ),
        (r'^accounts/password_reset/done/$', 'django.contrib.auth.views.password_reset_done'),
        (r'^accounts/reset/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
        (r'^accounts/reset/done/$', 'django.contrib.auth.views.password_reset_complete'),

        # Subsections
        (r'^oos/addresses/', include('mimicprint.addresses.urls')),
        (r'^oos/products/', include('mimicprint.products.urls')),
        (r'^oos/orders/', include('mimicprint.orders.urls')),
        (r'^oos/vardata/', include('mimicprint.vardata.urls')),
        (r'^oos/reports/', include('mimicprint.reports.urls')),
        (r'^oos/charts/', include('mimicprint.charts.urls')),
        (r'^oos/downloads/', include('mimicprint.downloads.urls')),
        (r'^oos/events/', include('mimicprint.events.urls')),

        #(r'^ariba/', include('mimicprint.ariba.urls')),

        url(r'^oos/feedback/$',
            contact_form,
            {
                'form_class': FeedbackForm,
                'success_url': '/oos/feedback/sent/',
            },
            name='contact_form'),
        url(r'^oos/feedback/sent/$',
            direct_to_template,
            { 'template': 'contact_form/contact_form_sent.html' },
            name='contact_form_sent'),
    )

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(settings.PROJECT_PATH, 'media')}),
        (r'^static/(.*)$', 'django.views.static.serve', {'document_root': os.path.join(settings.PROJECT_PATH, 'static')}),
    )

