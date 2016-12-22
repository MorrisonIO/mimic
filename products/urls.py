from django.conf.urls import url, patterns

urlpatterns = patterns('products.views',
    url(r'^$', 
        view = 'index',
        name = 'product_list',
    ),
    url(r'^search/', 
        view = 'search',
        name = 'product_search',
    ),
)
