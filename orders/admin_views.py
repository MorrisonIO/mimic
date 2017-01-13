import datetime

from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.models import User
from django.contrib import messages

from orgs.models import Org
from addresses.models import Address
from products.models import Product

from .forms import FastOrderForm
from .views import subtract_inventory
from .models import Cart, Order, OrderedItem, WorkNote  #InventoryHistory


@staff_member_required
def products_ordered(request, order_id):
    """
        Shows all the products on an order. If the ordered item is variable,
        the template displays a link so that an admin can download a printready PDF.
    """
    order = Order.objects.get(pk=order_id)
    ordered_items = OrderedItem.objects.filter(order=order)
    return render(request, 'admin/orders/products_ordered/details.html', {
        'order': order,
        'ordered_items': ordered_items,
    })


@staff_member_required
def create_docket(request, order_id):
    """
        Given an order_id, creates a docket page suitable for printing.
    """
    order = Order.objects.get(pk=order_id)
    ordered_items = OrderedItem.objects.filter(order=order)
    return render(request, 'admin/orders/dockets/docket.html', {
        'order': order,
        'ordered_items': ordered_items,
    })


@staff_member_required
def save_invnum(request):
    """
        Saves an invoice number to an order
        (accessed directly from a column on the orders change_list page).

        Note that we do *no* checking on the invoice number: whether it matches a certain pattern,
        whether it is unique, etc. We trust the user (and it can be edited afterwards if necessary).
    """
    if request.POST['invoice_number'] == '':
        # just return, don't save a blank value
        return HttpResponseRedirect('/admin/orders/order/')
    order_id = request.POST['order_id']
    order = Order.objects.get(pk=order_id)
    order.invoice_number = request.POST['invoice_number']
    order.status = 'in'
    order.save()
    messages.success(request, "The invoice number was saved successfully.")
    return HttpResponseRedirect('/admin/orders/order/')


@staff_member_required
def create_packingslip(request, order_id):
    """
    Shows the form to create a packing slip, or shows a printable page.
    """
    order = Order.objects.get(pk=order_id)
    ordered_items = OrderedItem.objects.filter(order=order)
    staff = list(User.objects.filter(is_staff=True))
    addresses = Address.objects.filter(owners__in=staff).order_by('last_name')
    printable = False
    date = order.date
    ship_to = order.ship_to
    if request.POST.get('submit'):
        printable = True
        date = request.POST.get('date')
        if request.POST.get('address'):
            ship_to = Address.objects.get(pk=request.POST.get('address'))
        else:
            ship_to = order.ship_to
    return render(request, 'admin/orders/shipping/packingslip.html', {
        'date': date,
        'order': order,
        'ship_to': ship_to,
        'printable': printable,
        'addresses': addresses,
        'ordered_items': ordered_items,
    })


@staff_member_required
def create_label(request, order_id):
    """
    Shows the form to create a label, or shows a printable page.
    """
    order = Order.objects.get(pk=order_id)
    staff = list(User.objects.filter(is_staff=True))
    addresses = Address.objects.filter(owners__in=staff).order_by('last_name')
    printable = False
    ship_to = order.ship_to
    contents = ''
    if request.POST.get('submit'):
        printable = True
        if request.POST.get('address'):
            ship_to = Address.objects.get(pk=request.POST.get('address'))
        else:
            ship_to = order.ship_to
        contents = request.POST.get('contents')
    return render(request, 'admin/orders/shipping/label.html', {
        'order': order,
        'ship_to': ship_to,
        'printable': printable,
        'addresses': addresses,
        'contents': contents,
    })


@staff_member_required
def create_comm_inv(request, order_id):
    """
    Shows the form to create a commercial invoice, or shows a printable page.
    """
    order = Order.objects.get(pk=order_id)
    ordered_items = OrderedItem.objects.filter(order=order)
    staff = list(User.objects.filter(is_staff=True))
    addresses = Address.objects.filter(owners__in=staff).order_by('last_name')
    printable = False
    total = 0.0
    date = order.date
    ship_to = order.ship_to
    item_dict = {}
    if request.POST.get('submit'):
        printable = True
        date = request.POST.get('date')
        if request.POST.get('address'):
            ship_to = Address.objects.get(pk=request.POST.get('address'))
        else:
            ship_to = order.ship_to
        for item in ordered_items:
            product = item.inventory_history.product
            exclude = "exclude_%s" % p.id
            if not request.POST.get(exclude):
                qty = "qty_%s" % product.id
                desc = "desc_%s" % product.id
                name = "item_%s" % product.id
                hs = "hs_num_%s" % product.id
                val = "value_%s" % product.id
                try:
                    total += float(request.POST.get(val))
                except ValueError:
                    total += 0
                field_dict = {'qty': request.POST.get(qty),
                              'name': request.POST.get(name),
                              'desc': request.POST.get(desc),
                              'hs_num': request.POST.get(hs),
                              'value': request.POST.get(val)}
                item_dict[p.id] = field_dict
    return render(request, 'admin/orders/shipping/comm_inv.html', {
        'date': date,
        'order': order,
        'total': total,
        'ship_to': ship_to,
        'printable': printable,
        'addresses': addresses,
        'ordered_items': ordered_items,
        'item_dict': item_dict,
    })


def worknote_format(notes):
    import re
    notes = re.sub('(/DL|/ET|/DC|/LA|/LD|/LC|/OO|/CB|/AM|/KA|/DS|/NEW)', '</span>', notes)
    notes = re.sub('(LC|OO|CB|AM|KA|DS)', '<span class="production">', notes)
    notes = notes.replace('DL', '<span class="dieter">')
    notes = notes.replace('ET', '<span class="erin">')
    notes = notes.replace('DC', '<span class="david">')
    notes = notes.replace('LA', '<span class="laura">')
    notes = notes.replace('LD', '<span class="lenny">')
    notes = notes.replace('NEW', '<span class="new">')
    return notes


@staff_member_required
def worknote_view(request, worknote_id):
    """
    View an individual worknote in 'plain' format, which is easier for simply reading (ie not the admin editing form).
    """
    worknote = WorkNote.objects.get(pk=worknote_id)
    return render(request, 'admin/orders/worknote/view.html', {
        'worknote': worknote,
        'notes': worknote_format(worknote.notes),
    })


@staff_member_required
def fastorder_add(request):
    """
    A fastorder is an Order that's added by Mimic staff manually via the admin pages,
    used for orders that do *not* come in via the website.
    We need this to avoid having to deal with OrderedItems and InventoryHistory,
    adding Products on the fly, and entering fields we know already to present an easier UI.
    """
# Does not work: putting choices for dropdowns in FastOrderForm (as choices= in the field definition). We can the show the dropdown in the template with {{ form.job1_product }}, but if you add a new product via the + javascript, it fails validation because it's not part of the originally specified choices ("Select a valid choice. That choice is not one of the available choices.")
# Does not work: specify choices here in the view, pass them into the template, and construct the <select>s manually. Same error as above.
# Too complicated for me: creating a Field subclass in the form and manually doing Field.clean(). New items created with the + are displayed ok and then pass validation, but if some other validation fails and the page reloads, the new item we created is not in the dropdown.
    errors = ''
    if request.method == "POST":  # validate and save
        form = FastOrderForm(request.POST)
        if form.is_valid():
            # generate and save order
            o = Order()
            c = Cart()
            o.name = c.make_name()
            o.placed_by = request.user
            oid = request.POST.get('org', None)
            o.org = Org.objects.get(pk=oid)
            o.status = 'ac'
            o.date = datetime.datetime.now()
            o.due_date = request.POST.get('due_date', None)
            stid = request.POST.get('ship_to', None)
            o.ship_to = Address.objects.get(pk=stid)
            o.po_number = request.POST.get('po_number', None)
            o.additional_info = request.POST.get('additional_info', None)
            o.save()

            # handle subtracting inventory and generating InventoryHistory & OrderedItems
            for n in range(1, 6):  # jobs 1 - 5
                prod_str = 'job%s_product' % n
                qty_str = 'job%s_qty' % n
                pid = request.POST.get(prod_str, None)
                if pid:
                    product = Product.objects.get(pk=pid)
                    amt = request.POST.get(qty_str, None)
                    subtract_inventory(product, o, amt, o.placed_by, 'Online order', o.date)

            messages.success(request, "The FastOrder was successfully saved.")
            return HttpResponseRedirect('/admin/orders/order/')
        else:
            errors = form.errors
    else:  # show form
        form = FastOrderForm()

    return render(request, 'admin/orders/order/fastorder.html', {
        'form': form,
        'errors': errors,
    })
