import random
import re

from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.template import loader, Context, Template
from django.template.loader import get_template, render_to_string
from django.contrib import messages
from django.http import HttpResponse
from products.models import Product, Category
from orgs.models import UserProfile
from decorators import current_org_required
from helpers.views import get_query
from itertools import repeat


@login_required
@current_org_required
def index(request):
    """
    Shows the list of Products:
    each Category followed by a table of all the Products in that category.
    """
    user = request.user
    org = request.session['current_org']
    try:
        profile = UserProfile.objects.get(user=user, org=org)
    except MultipleObjectsReturned as mor_ex:
        profile = UserProfile.objects.filter(user=user, org=org)[0]
    except ObjectDoesNotExist as odne_ex:
        profile = None
    unrestricted_qtys = user.has_perm('orders.change_order') or profile.unrestricted_qtys
    user_is_manager = user.has_perm('orders.change_order')
    categories = Category.objects.filter(org=org).order_by('sort', 'name')
    products = Product.objects.filter(categories__in=categories, status__exact='av').distinct().order_by('sort', 'name') 
    return render(request, 'products/product_list.html', {
        'profile': profile,
        'products': products,
        'categories': categories,
        'ignore_pa': profile.ignore_pa if profile is not None else None,
        'unrestricted_qtys': unrestricted_qtys,
        'user_is_manager': user_is_manager,
    })


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

    return render(request, 'products/product_list.html', {
        'profile': profile,
        'ignore_pa': profile.ignore_pa,
        'unrestricted_qtys': unrestricted_qtys,
        'search': True,
        'query_string': query_string,
        'products': found_products,
        'categories': [1, ]  # hack to reuse product list template,
                             # which loops through categories
    })

def get_category(request):
    """
    Return category object
    """
    org = request.session['current_org']
    user = request.user
    user_is_manager = user.has_perm('orders.change_order')
    try:
        profile = UserProfile.objects.get(user=user, org=org)
    except MultipleObjectsReturned as mor_ex:
        profile = UserProfile.objects.filter(user=user, org=org)[0]
    except ObjectDoesNotExist as odne_ex:
        profile = None
    unrestricted_qtys = user.has_perm('orders.change_order') or profile.unrestricted_qtys
    category_id = request.GET.get('id', None)
    cat = Category.objects.filter(id=category_id)
    products = Product.objects.filter(categories__in=cat, status__exact='av').distinct().order_by('sort', 'name')
    rendered = render_to_string('products/product_list_item.html', {
        'products': products,
        'cat': cat[0],
        'user_is_manager': user_is_manager,
        'unrestricted_qtys': unrestricted_qtys
        }, request=request)
    return HttpResponse(rendered)
