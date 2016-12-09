from django.http import HttpResponseRedirect, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404
from django import forms
from django.forms import widgets
from django.contrib.admin.views.decorators import staff_member_required
from django.template import RequestContext, loader, Context
from django.contrib.auth.models import User
from mimicprint.orgs.models import Org, UserProfile
from mimicprint.products.models import Product, ProductSelection
from django.db import connection
from django.db.transaction import commit_on_success
from datetime import datetime

@staff_member_required
def duplicate_product(request, product_id):
    """
    Duplicates the product provided -- creates a new row in the db with the exact same data only a different primary key. We redirect to the new change form and rely on the user to edit it accordingly (ie, distinguish it somehow from the original).
    """
    product = Product.objects.get(pk=product_id)
    product.pk = None
    product.save()
    request.user.message_set.create(message="The product was duplicated successfully. This page is for your new product; edit as necessary.")
    url = '/admin/products/product/%s/' % product.id
    return HttpResponseRedirect(url)

def get_products_and_selections():
    cursor = connection.cursor()

    cursor.execute(
        """
        SELECT `p`.*, `s`.id IS NOT NULL `selected`
        FROM `products_product` `p`
        LEFT OUTER JOIN `products_productselection` `s` ON `s`.`product_id` = `p`.`id`
        """
    )

    cols = [c[0] for c in cursor.description]
    for row in cursor:
        data = dict(zip(cols, row))

        data['title'] = u'[%s] %s (#%d)' % (
            data['part_number'],
            data['name'],
            data['id']
        )

        yield data

@commit_on_success
def update_selections(products):
    cursor = connection.cursor()
    cursor.execute('DELETE FROM products_productselection')
    for p in products:
        ProductSelection(product=p).save()

@staff_member_required
def export_settings(request):
    return render_to_response('admin/products/export/settings.html', {
        'request': request,
        'items': get_products_and_selections()
    }, context_instance=RequestContext(request))

@staff_member_required
def export_products(request):
    products = Product.objects.filter(pk__in=request.POST.getlist('products[]'))
    update_selections(products)

    response = render_to_response('admin/products/export/template.cif', {
        'products': products,
        'now': datetime.now()
    })

    response['Content-Type'] = 'octet/stream'
    response['Content-Disposition'] = 'attachment; filename=import.cif'
    return response
