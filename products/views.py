import random
import re
import json
import os

from django.conf import settings
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.core import serializers
from django.template import loader, Context, Template
from django.template.loader import get_template, render_to_string
from django.contrib import messages
from django.http import HttpResponse
from products.models import Product, Category
from orgs.models import UserProfile
from decorators import current_org_required
from helpers.views import get_query
from itertools import repeat

def collect_menu_data(products):
    """
    Collect data for menu information
    E.g.: number of some kind of products
    """

    # products = Product.objects.all()
    elems = {}
    elems['min_quantity'] = {'title': 'Min Order Quanity'}
    elems['price'] = {'title': 'Price'}

    try:
        for product in products:
            if product.price:
                if float(product.price) in elems['price']:
                    elems['price'][str(float(product.price))] += 1
                else:
                    elems['price'][str(float(product.price))] = 1

            if product.min_order_qty:
                if product.min_order_qty in elems['min_quantity']:
                    elems['min_quantity'][str(product.min_order_qty)] += 1
                else:
                    elems['min_quantity'][str(product.min_order_qty)] = 1

    except Exception as ex:
        pass
    finally:
        return elems


@login_required
@current_org_required
def index(request, group_list=None):
    """
    Shows the list of Products:
    each Category followed by a table of all the Products in that category.
    """

    user = request.user
    user_is_manager = user.has_perm('orders.change_order')
    current_org = request.session.get('current_org', None)

    try:
        profile = UserProfile.objects.get(user=user, org=current_org)
    except MultipleObjectsReturned as mor_ex:
        profile = UserProfile.objects.filter(user=user, org=current_org)[0]
    except Exception as ex:
        profile = None

    try:
        unrestricted_qtys = user_is_manager or profile.unrestricted_qtys
    except Exception as ex:
        unrestricted_qtys = False

    categories = Category.objects.filter(org=current_org).order_by('sort', 'name')
    products_by_category = []
    product_list = []
    for category in categories:
        products = Product.objects.filter(categories__in=[category], status__exact='av').distinct()\
                                                                        .order_by('sort', 'name')
        product_list += products
        products_by_category.append(dict(name=category.name, products=products))
    menu_data = collect_menu_data(product_list)
    if group_list:
        template_to_render = 'products/product_list_new.html'
    else:
        template_to_render = 'products/product_list.html'
    return render(request, template_to_render, {
        'profile': profile,
        'products': products_by_category, #products,
        'categories': categories,
        'ignore_pa': profile.ignore_pa if profile is not None else None,
        'unrestricted_qtys': unrestricted_qtys,
        'user_is_manager': user_is_manager,
        'menu_data': menu_data
    })

@current_org_required
def search(request):
    """
    Search @query_string within products fields
    """
    query_string, found_products = '', ''
    user = request.user
    user_is_manager = user.has_perm('orders.change_order')
    current_org = request.session.get('current_org', None)

    try:
        profile = UserProfile.objects.get(user=user, org=current_org)
    except MultipleObjectsReturned as mor_ex:
        profile = UserProfile.objects.filter(user=user, org=current_org)[0]
    except Exception as ex:
        profile = None

    try:
        unrestricted_qtys = user_is_manager or profile.unrestricted_qtys
    except Exception as ex:
        unrestricted_qtys = False

    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        product_query = get_query(query_string, ['name', 'part_number'])
        found_products = Product.objects.filter(product_query) \
                        .filter(categories__org=current_org).order_by('-name')

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

    user = request.user
    user_is_manager = user.has_perm('orders.change_order')
    current_org = request.session.get('current_org', None)

    try:
        profile = UserProfile.objects.get(user=user, org=current_org)
    except MultipleObjectsReturned as mor_ex:
        profile = UserProfile.objects.filter(user=user, org=current_org)[0]
    except Exception as ex:
        profile = None

    try:
        unrestricted_qtys = user_is_manager or profile.unrestricted_qtys
    except Exception as ex:
        unrestricted_qtys = False

    category_id = request.GET.get('id', None)
    cat = Category.objects.filter(id=category_id)
    products = Product.objects.filter(categories__in=cat, status__exact='av') \
                                                            .distinct().order_by('sort', 'name')
    rendered = render_to_string('products/product_list_item.html', {
        'products': products,
        'cat': cat[0],
        'user_is_manager': user_is_manager,
        'unrestricted_qtys': unrestricted_qtys
        }, request=request)
    return HttpResponse(rendered)

def get_product_modal_data(request):
    """
    Find product by ID and return preview image for it
    """
    product_id = request.GET.get('id')
    product = Product.objects.get(pk=product_id)
    description = product.description if product else ''
    if os.path.isfile(settings.MEDIA_ROOT + product.preview.name):
        image_path = '/media/{}'.format(product.preview.name)
    else:
        image_path = '/static/img/product_preview.jpg'

    preview_image = [{'url': image_path, 'name': 'Preview Image'}] if product.preview else []
    return HttpResponse(json.dumps({'description': description, 'preview_image': preview_image}))
