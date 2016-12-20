from django.conf.urls.defaults import *

urlpatterns = patterns('mimicprint.products.views',
    url(r'^$', 
        view = 'index',
        name = 'product_list',
    ),
    url(r'^search/', 
        view = 'search',
        name = 'product_search',
    ),
)
