from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django import forms
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from mimicprint.products.models import Product, Category
from mimicprint.orgs.models import UserProfile
from mimicprint.decorators import current_org_required
from mimicprint.helpers.views import get_query


@login_required
@current_org_required
def index(request):
    """
    Shows the list of Products: each Category followed by a table of all the Products in that category.
    """
    user = request.user
    org = request.session['current_org']
    profile = UserProfile.objects.get(user=user, org=org)
    unrestricted_qtys = user.has_perm('orders.change_order') or profile.unrestricted_qtys
    user_is_manager = user.has_perm('orders.change_order')
    categories = Category.objects.filter(org=org).order_by('sort', 'name')
    products = Product.objects.filter(categories__in=categories, status__exact='av').distinct().order_by('sort', 'name') 
    return render_to_response('products/product_list.html', {
        'profile': profile,
        'products': products, 
        'categories': categories, 
        'ignore_pa': profile.ignore_pa,
        'unrestricted_qtys': unrestricted_qtys,
        'user_is_manager': user_is_manager,
    }, context_instance=RequestContext(request))


def search(request):
    query_string, found_products = '', ''
    user = request.user
    org = request.session['current_org']
    profile = UserProfile.objects.get(user=user, org=org)
    unrestricted_qtys = user.has_perm('orders.change_order') or profile.unrestricted_qtys
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        product_query = get_query(query_string, ['name', 'part_number'])
        found_products = Product.objects.filter(product_query).filter(categories__org=request.session['current_org']).order_by('-name')

    return render_to_response('products/product_list.html', { 
        'profile': profile,
        'ignore_pa': profile.ignore_pa,
        'unrestricted_qtys': unrestricted_qtys,
        'search': True,
        'query_string': query_string,
        'products': found_products,
        'categories': [1,] # hack to reuse product list template, which loops through categories
    }, context_instance=RequestContext(request))

