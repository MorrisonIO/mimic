import datetime
import random
import re
import string
import os 

from django import forms
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.files import File
from django.contrib import messages
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.forms import widgets, ModelForm
from django.http import HttpResponseRedirect, HttpResponseServerError, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext, loader, Context, Template
from django.template.loader import get_template

from addresses.forms import AddressForm
from addresses.models import Address
from decorators import current_org_required
from helpers.views import get_query
from orders.forms import OrderForm, OrderPDFForm
from orders.models import Cart, Order, InventoryHistory, OrderedItem
from orgs.models import Org, UserProfile
from products.models import Product
from uploads.models import Upload
from vardata.models import *


@login_required
@current_org_required
def process_products(request):
    """
    Process each item requested for ordering: if the item is a variable data item,
    add it to a session variable list of products the user must provide data for;
    otherwise add it to the cart.
    """
    if not request.session.get('data_to_get', None):
        request.session['data_to_get'] = []
    products = []
    if request.method == 'POST':
        for p in request.POST:
            if p.startswith('qty_'):
                product_id = p.split('_')[1]
                product = get_object_or_404(Product, pk=product_id)
                quantity = request.POST[p]
                quantity = re.sub(r'[^0-9]', '', quantity)
                quantity = int(quantity) if quantity else 0
                if quantity:  # product was ordered
                    u_field = 'u_%s' % product_id
                    unique_id = request.POST.get(u_field, None)
                    o_field = 'o_%s' % product_id
                    orderer = request.POST.get(o_field, None)
                    if product.is_variable:
                        # Add it to session var list of products to get data for,
                        # unless data is already approved (user modifying from cart)
                        approved = False
                        if request.session.get('data_approved', None):
                            for item in request.session['data_approved']:
                                if item['unique_id'] == unique_id:
                                    approved = True
                        if not approved:
                            item = {'product_id': product_id,
                                    'unique_id': unique_id,
                                    'quantity': quantity
                                    }
                            # product added to cart only after the user supplies data and approves it
                            request.session['data_to_get'].append(item)

                    if not product.is_variable or approved:
                        overwrite = request.POST.get('cart_modify', None)
                        products.append({'product_id': product.id,
                                         'unique_id': unique_id,
                                         'orderer': int(orderer),
                                         'quantity': quantity,
                                         'overwrite': overwrite
                                         })

        ordered_products = sorted(products, key=lambda k: k['orderer'])
        for item in ordered_products:
            product = get_object_or_404(Product, pk=item['product_id'])
            put_in_cart(request, product, item['unique_id'], item['quantity'], item['overwrite'])

        return HttpResponseRedirect(reverse('orders:vardata_input'))
    else:  # shouldn't arrive at this view except via POST
        return HttpResponseRedirect(reverse('products:product_list'))


def put_in_cart(request, product, unique_id, quantity, overwrite=False):
    """
    Puts the specified product into the cart.
    If the product is already in the cart and it's not variable,
    the amount ordered is incremented. Overwrite allows the user
    to directly set the ordered amount from the cart summary.
    """
    user = request.user
    org = request.session['current_org']
    profile = UserProfile.objects.get(user=user, org=org)
    unrestricted_qtys = user.has_perm('orders.change_order') or profile.unrestricted_qtys

    # make sure amount ordered was not lower than any min set
    if product.min_order_qty and quantity < product.min_order_qty and not unrestricted_qtys:
        message = 'w|The amount of "%s" ordered was updated to reflect minimum quantity restrictions.' % product
        messages.warning(request, message)
        quantity = product.min_order_qty

    # update cart
    cart = request.session.get('cart', None) or Cart()
    already_ordered = cart.has_item(product)
    # increment it
    if already_ordered and not product.is_variable and not overwrite:
        # make sure new amount does not violate any fixed ordering quantities
        if product.fixed_order_qtys and not unrestricted_qtys:
            fixed_qtys = re.sub(r'[^0-9,]', '', product.fixed_order_qtys).split(',')
            new_qty = already_ordered.quantity + quantity
            if unicode(new_qty) not in fixed_qtys:
                message = 'w|The total amount of "%s" ordered was not in the allowable range of values.' % product
                messages.warning(request, message)
                quantity = 0
        cart.incr_item(product, quantity)
    # add it
    else:
        cart.add_item(product, unique_id, quantity)
    request.session['cart'] = cart


@login_required
def vardata_remodify(request, unique_id):
    """
    Allows user to remodify an ordered variable data item from the cart summary.
    This view merely handles managing the various session variables,
    and then returns to the data input form.
    """
    for item in request.session['data_approved']:
        if item['unique_id'] == unique_id:
            request.session['data_approved'].remove(item)  # remove it from approved list
            request.session['data_to_get'].append({        # add back to list of outstanding items
                'product_id': item['product_id'],
                'unique_id': item['unique_id'],
                'quantity': item['quantity']
            })
            request.session['form_data'] = item            # repopulate form w/user info
    return HttpResponseRedirect(reverse('orders:vardata_input'))


@login_required
def vardata_input(request):
    """
    If there is a session variable list of remaining ordered items
    to get data from the user for,
    this view shows the input form for the first item on the list
    (including validating and redisplaying with errors);
    otherwise redirects to the cart summary.
    """
    # there is at least one outstanding item to get data for
    if request.session.get('data_to_get', None):
        product_id = request.session['data_to_get'][0]['product_id']
        product = get_object_or_404(Product, pk=product_id)
        var_form = eval(product.var_form)
        if not var_form:
            return HttpResponseServerError('Missing form')  # TODO proper one

        if request.method == 'POST':
            form = var_form(request.POST)
            if form.is_valid():
                request.session['form_data'] = form.cleaned_data
                url = "%s%s/" % (reverse('vardata:vardata_prefix'), product.var_form)
                # create preview images
                return HttpResponseRedirect(url)
            else:
                messages.warning(request, "e|There was a problem with your submission.\
                                           Refer to the messages below and try again.")
        else:
            if request.session.get('form_data', None):
                form = var_form(request.session['form_data'])
            else:
                form = var_form()

        return render(request, 'orders/vardata_input.html', {
            'form': form,
            'product': product,
        })

    # no outstanding items, show cart
    else:
        return HttpResponseRedirect(reverse('orders:cart_summary'))


@login_required
@current_org_required
def vardata_preview(request):
    """
    Creates and shows the preview image of a variable item
    after the user has inputted data. If the user says the preview is ok,
    this view reloads and that data is saved and the item is added to the cart.
    Otherwise the user is return to the input form to make corrections.
    """
    if request.POST.get('preview_ok', None):
        # save approved data to session var for saving later
        data = request.session.get('form_data', None)
        data['product_id'] = request.session['data_to_get'][0]['product_id']
        data['unique_id'] = request.session['data_to_get'][0]['unique_id']
        data['quantity'] = request.session['data_to_get'][0]['quantity']
        if not request.session.get('data_approved', None):
            request.session['data_approved'] = []
        request.session['data_approved'].append(data)

        # add it to the cart
        product_id, unique_id, quantity = request.session['data_to_get'][0].values()
        product = Product.objects.get(pk=product_id)
        put_in_cart(request, product, unique_id, quantity)

        del request.session['data_to_get'][0]  # delete product from list of outstanding items
        del request.session['form_data']       # delete saved form info

        # redirect back to vardata_input to see
        # if there are any more items to get data for
        return HttpResponseRedirect(reverse('orders:vardata_input'))

    else:
        # session var set in the vardata view
        filename_prefix = request.session.get('filename_prefix', None)
        pdf_file = "%spreviews/%s.pdf" % (settings.MEDIA_URL, filename_prefix)
        img_file = "%spreviews/%s.gif" % (settings.MEDIA_URL, filename_prefix)

        return render(request, 'orders/vardata_preview.html', {
            'pdf_file': pdf_file,
            'img_file': img_file,
        })


@login_required
@current_org_required
def cart_summary(request):
    """
    Shows the contents of an order so far (ie the 'cart').
    """
    user = request.user
    org = request.session['current_org']
    profile = UserProfile.objects.get(user=user, org=org)
    unrestricted_qtys = user.has_perm('orders.change_order') or profile.unrestricted_qtys
    cart = request.session.get('cart', None) or Cart()
    return render(request, 'orders/cart_index.html', {
        'cart': cart,
        'ignore_pa': profile.ignore_pa,
        'unrestricted_qtys': unrestricted_qtys,
    })


def delete_order_session_vars(request):
    """
    Deletes all the order session variables.
    Used both when cancellling an order,
    and after an order has been successfully submitted
    to clean up afterwards.
    """

    keys = [
        'shipto_address',
        'cart',
        'data_to_get',
        'data_approved',
        'form_data',
        'due_date',
        'po_number',
        'additional_info',
        'user_notes',
        'cc_confirmation'
    ]
    for key in keys:
        try:
            del request.session[key]
        except KeyError:
            pass


@login_required
def cancel_order(request):
    """
    Cancels an order in progress.
    This completely trashes the cart session variables.
    """
    delete_order_session_vars(request)
    messages.warning(request, "s|Your order has been cancelled.")
    return HttpResponseRedirect(reverse('orders:cart_summary'))


@login_required
def delete_from_cart(request, unique_id):
    """
    Deletes an individual item from the cart.
    """
    cart = request.session.get('cart', None) or Cart()
    cart.delete_item(unique_id)
    request.session['cart'] = cart

    # if deleting a variable item, also remove it from the list of approved data
    if request.session.get('data_approved', None):
        for item in request.session['data_approved']:
            if item['unique_id'] == unique_id:
                request.session['data_approved'].remove(item)

    messages.info(request, 's|The item was removed from your order.')
    return HttpResponseRedirect(reverse('orders:cart_summary'))


@login_required
def provide_shipto(request):
    """
    Allows the user to provide a shipto address for an order,
    either by selecting one from an address book,
    or by entering a new one manually. Once provided,
    a shipto_address session variable is created -
    - if that is present this view shows the destination address
    and the continue button allowing the user to proceed
    to the next ordering step.
    """
    addresses = Address.objects.filter(owners__in=[request.user])
    # address selected from dropdown or new address being entered
    if request.method == 'POST':
        # addr from AB not selected, validate new address form
        if not request.POST.get('shipto_address', None):
            form = AddressForm(request.POST)
            if form.is_valid():
                new_addr = form.save()
                if request.POST.get('add_to_ab', None):
                    new_addr.owners.add(request.user)
                    messages.success(request, "s|The address was added to your Address Book.")
                    new_addr.save()
                request.session['shipto_address'] = new_addr
            else:
                messages.warning(request, "e|There was a problem with your submission. \
                                           Refer to the messages below and try again.")

        else:
            form = AddressForm()
            address_id = request.POST.get('shipto_address', None)
            address = get_object_or_404(Address, pk=address_id)
            request.session['shipto_address'] = address
    else:
        form = AddressForm()
    return render(request, 'orders/provide_shipto.html', {
        'form': form,
        'addresses': addresses,
    })


@login_required
def create_upload(request, file):
    """
    Creates Upload model from request.FILE['upload_file']
    Returns instance
    """
    user_name = request.user.username
    email = request.user.email
    is_deletable = True
    upload = Upload.objects.create(name=file.name, file=file, user_name=user_name,\
                                    email=email, is_deletable=is_deletable)
    return upload


@login_required
def provide_addinfo(request):
    """
    Allows the user to provide a due date and any additional info for an order.
    """
    if request.method == 'POST':
        form = OrderForm(data=request.POST, request=request)
        if form.is_valid():  # set session vars
            request.session['due_date'] = request.POST.get('due_date', None)
            request.session['po_number'] = request.POST.get('po_number', None)
            request.session['additional_info'] = request.POST.get('additional_info', None)
            request.session['user_notes'] = request.POST.get('user_notes', None)
            request.session['cc_confirmation'] = request.POST.get('cc_confirmation', None)
            file = request.FILES.get('upload_file', None)
            if file != None:
                path = handle_uploaded_file(file)
                full_path = settings.BASE_DIR + path
                request.session['upload_file'] = full_path
            return HttpResponseRedirect(reverse('orders:confirm_order'))
        else:
            messages.warning(request, "e|There was a problem with your submission. \
                                       Refer to the messages below and try again.")

    else:
        if request.session['upload_file']:
            try:
                os.remove(request.session['upload_file'])
            except Exception as ex:
                pass
            request.session['upload_file'] = None
        form = OrderForm(request=request)
    return render(request, 'orders/provide_addinfo.html', {
        'form': form,
    })


@login_required
def confirm_order(request):
    """
    Final step in the ordering process: shows the user a final order summary,
    allows them to confirm and save/place the order.
    """
    context = None
    path = request.session.get('upload_file', None)
    filename = None
    if path:
        filename = os.path.basename(request.session['upload_file'])
    return render(request, 'orders/confirm_order.html', { 'filename': filename })


@login_required
@current_org_required
def order_list(request):
    """
    If the user is a regular user, shows a list of orders placed by that user.
    If the user is a manager, shows a list of all orders placed by members
    of the active organization.
    """
    org = request.session['current_org']
    user_is_approval_manager = org.approval_manager == request.user
    today = datetime.datetime.today()
    cutoff = today - datetime.timedelta(days=21)
    if user_is_approval_manager:
        order_list = Order.objects.filter(org=org) #.filter(date__range=(cutoff, today))
    else:
        order_list = Order.objects.filter(placed_by__exact=request.user) #.filter(date__range=(cutoff, today))

    return render(request, 'orders/order_list.html', {
        'order_list': order_list,
        'user_is_approval_manager': user_is_approval_manager,
    })


@login_required
def show_order(request, order_id, confirm=False):
    """
    Shows an individual order (ie., one that's already been placed).
    Also used for the confirmation page after submitting an order.
    """
    profiles = UserProfile.objects.filter(user=request.user)
    valid_orgs = [p.org for p in profiles]
    user_is_manager = request.user.has_perm('orders.change_order')
    if user_is_manager:
        order = get_object_or_404(Order, pk=order_id, org__in=valid_orgs)
    else:
        order = get_object_or_404(Order, pk=order_id, placed_by__exact=request.user)
    oi = OrderedItem.objects.filter(order__exact=order.id)
    line_items = order.get_line_items()
    
    file_url = None

    if order.additional_file != None:
        file_url = order.additional_file.file.url

    return render(request, 'orders/order_detail.html', {
        'is_confirmation': confirm,
        'order': order,
        'line_items': line_items,
        'user_is_manager': user_is_manager,
        'file_url': file_url
    })


@login_required
def process_order(request):
    """
    Performs the steps necessary to save a new order:
    creates and saves an order and any variable info,
    subtracts inventory, send emails, clean up afterwards.
    """
    # TODO more sanity checking: duplicate orders,
    # reverse db saves if one of the steps doesn't complete successfully, etc
    if not request.session.get('cart', None) \
       or not request.session.get('shipto_address', None) \
       or not request.session.get('due_date', None):
        return HttpResponseRedirect(reverse('orders:confirm_order'))
    order = save_new_order(request)
    save_ordered_items(request, order)
    send_order_emails(request, order)
    delete_order_session_vars(request)

    messages.success(request, "s|Your order has been successfully submitted.")
    return HttpResponseRedirect(reverse('orders:order_confirmation', args=[order.id]))


def save_new_order(request):
    """
    Saves a new order.
    Note this does not handle saving OrderedItemsor InventoryHistory events.
    All necessary pieces of the order should exist as session variables.
    """
    order = Order()
    order.name = order.make_name()
    order.placed_by = request.user
    order.org = request.session['current_org']
    order.status = 'ac'  # active
    order.date = datetime.datetime.now()
    due_date_parts = request.session['due_date'].split("-")
    order.due_date = datetime.date(int(due_date_parts[0]),
                                   int(due_date_parts[1]),
                                   int(due_date_parts[2])
                                  )
    order.ship_to = request.session['shipto_address']
    order.po_number = request.session['po_number']
    order.additional_info = request.session['additional_info']
    order.user_notes = request.session['user_notes']

    if 'upload_file' in request.session:
        path = request.session['upload_file']
        if path and os.path.isfile(path):
            file = File(open(path, 'r'))
            upload = create_upload(request, file)
            try:
                os.remove(request.session['upload_file'])
            except Exception as ex:
                pass
            order.additional_file = upload
    request.session['upload_file'] = None
    order.save()
    return order


def save_ordered_items(request, order):
    """
    Saves the OrderedItems and InventoryHistory events belonging to an order.
    """
    cart = request.session['cart']
    profile = UserProfile.objects.get(user=request.user, org=request.session['current_org'])
    for item in cart.all_items():
        product = Product.objects.get(pk=item.product.id)
        if product.approval_required and not profile.ignore_pa:
            order.status = 'pa'
            order.save()
        oi = subtract_inventory(product=product,
                                order=order,
                                amount=item.quantity,
                                modified_by=order.placed_by,
                                notes="Online order", date=order.date
                               )

        # also save variable info, if there is a set
        # of data matching this item's unique id
        try:
            for data in request.session['data_approved']:
                if item.unique_id in data.values():
                    var_form = eval(item.product.var_form)
                    form = var_form(data)
                    new_vardata = form.save(commit=False)
                    new_vardata.ordereditem = oi
                    new_vardata.product = item.product
                    new_vardata.save()
        except KeyError:
            pass


def subtract_inventory(product, order, amount, modified_by, notes, date):
    """
    Manages saving InventoryHistory and OrderedItem events for a product,
    ncluding recursively descending into components.
    Returns the OrderedItem for the product that was ordered,
    since we need the PK to possibly save variable info.
    """
    ih = InventoryHistory(product=product,
                          order=order,
                          amount=amount,
                          modified_by=modified_by,
                          notes=notes,
                          date=date
                         )
    ih.save()
    # there are components to this product
    if product.ratios.all():
        import math
        for r in product.ratios.all():
            # round up to nearest whole number
            amt = math.ceil(amount * float(r.ratio))
            if r.component.track_inventory:
                notes = "Consumed as component of '%s'" % product
                subtract_inventory(product=r.component,
                                   order=order,
                                   amount=amt,
                                   modified_by=modified_by,
                                   notes=notes,
                                   date=date
                                  )
    else:  # base case of recursion -- a product with no components (eg a raw material like paper)
        pass
    # the product that was ordered
    if not product.is_component: 
        oi = OrderedItem(order=order, inventory_history=ih)
        oi.save()
        return oi


def send_order_emails(request, order):
    """
    Sends out the various emails when an order is placed:
        * Client: If approval is required,
          email goes to orderer and approval manager;
          otherwise just to orderer
        * Mimic: For all orders, emails go to production@
          and the mimic account reps
    """
    site = Site.objects.get_current()
    user_profile = UserProfile.objects.get(user=order.placed_by, org=order.org)
    line_items = order.get_line_items()

    if settings.ALLOW_STAFF_EMAILS:
        mimic_list = ['Production <production@mimicprint.com>']
        for rep in order.org.mimic_rep.filter(is_active=1):
            address = '%s <%s>' % (rep.get_full_name(), rep.email)
            mimic_list.append(address)
    else:
        mimic_list = settings.STAFF
    orderer = '%s <%s>' % (order.placed_by.get_full_name(), order.placed_by.email)
    user_list = [orderer]
    if request.session['cc_confirmation']:
        addresses = request.session['cc_confirmation'].replace(' ','').split(',')
        for address in addresses:
            user_list.append(address)

    if order.status == 'pa':
        if order.org.approval_manager:
            fullname = order.org.approval_manager.get_full_name()
            manager_email = order.org.approval_manager.email
            approval_manager = '%s <%s>' % (fullname, manager_email)
            user_list.append(approval_manager)
        email = 'emails/order_approvalrequired.txt'
        mimic_email = 'emails/mimic_order_approvalrequired.txt'
        if order.org.approval_email:
            try:
                email = 'emails/%s' % order.org.approval_email
            except:
                pass
        template = loader.get_template(email)
        mimic_template = loader.get_template(mimic_email)
        subject = '[Mimic OOS] Order Approval Required: %s' % order.name
    else:
        email = 'emails/order_confirmed.txt'
        email_html = 'emails/order_confirmed.html'
        mimic_email = 'emails/mimic_order_confirmed.txt'
        mimic_email_html = 'emails/mimic_order_confirmed.html'
        if order.org.order_email:
            try:
                email = 'emails/%s' % order.org.order_email
            except:
                pass
        template = loader.get_template(email)
        template_html = loader.get_template(email_html)
        mimic_template = loader.get_template(mimic_email)
        mimic_template_html = loader.get_template(mimic_email_html)
        subject = '[Mimic OOS] Order Confirmed: %s' % order.name
    
    c = Context({
        'order': order,
        'user_profile': user_profile,
        'line_items': line_items,
        'site': site,
        'host': '{}{}'.format(request.get_host(), order.additional_file.file.url) if order.additional_file else None
    })
    body = template.render(c)
    body_html = template_html.render(c)
    mimic_body = mimic_template.render(c)
    mimic_body_html = mimic_template_html.render(c)
    #    print "\n==========\nSending mail to users...\nTo: %s\nSubject: %s\n%s" % ([u for u in user_list], subject, body)
    #    print "\n==========\nSending mail to Mimic...\nTo: %s\nSubject: %s\n%s" % ([u for u in mimic_list], subject, mimic_body)
    send_mail(subject, body, 'orders@mimicprint.com', user_list, fail_silently=False, html_message=body_html)  # notify user
    send_mail(subject, mimic_body, 'orders@mimicprint.com', mimic_list, fail_silently=False, html_message=mimic_body_html)  # notify mimic


@login_required
@current_org_required
def approve_order(request):
    """
    Sets the status of an Order to active.
    This allows managers to give the go-ahead
    via the orders list form or an order detail page.
    """
    org = request.session['current_org']
    site = Site.objects.get_current()
    now = datetime.datetime.now()

    if request.method == 'POST':
        for p in request.POST:
            if p.startswith('order_id_'):
                order_id = p.split('_')[2]
                order = Order.objects.get(pk=order_id, org=org)
                order.status = "ac"
                order.approved_by = request.user
                order.approved_date = now
                order.save()

                # Send email alerts to Mimic
                t = loader.get_template('emails/mimic_order_approvalreceived.txt')
                subject = "[Mimic OOS] Order Approval Received: %s" % order.name
                rep_list = ["Production <production@mimicprint.com>"]
                for r in org.mimic_rep.filter(is_active=1):
                    addr = "%s %s <%s>" % (r.first_name, r.last_name, r.email)
                    rep_list.append(addr)
                c = Context({
                    'order': order,
                    'site': site,
                })
                body = t.render(c)
    #                print "\n==========\nSending mail to Mimic...\nTo: %s\nSubject: %s\n%s" % ([u for u in rep_list], subject, body)
                send_mail(subject, body, 'orders@mimicprint.com', rep_list, fail_silently=False)

        messages.success(request, "s|The order(s) have been approved.")

    if request.POST.get('detail', None):
        url = reverse('orders:order_detail', args=[order_id])
    else:
        url = reverse('orders:order_index')
    return HttpResponseRedirect(url)


def search(request):
    query_string, found_orders = '', ''
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        search_fields = ['name', 'po_number', 'invoice_number', 'additional_info', 'user_notes']
        order_query = get_query(query_string, search_fields)
        if request.user.has_perm('orders.change_order'):
            found_orders = Order.objects.filter(order_query).filter(org=request.session['current_org']).order_by('-date')
        else:
            found_orders = Order.objects.filter(order_query).filter(placed_by=request.user).order_by('-date')

    return render(request, 'orders/order_list.html', {
        'search': True,
        'query_string': query_string,
        'order_list': found_orders
    })


def handle_uploaded_file(f):
    """
    Writes an uploaded file to the filesystem.
    This is currently putting uploads in the *public* media directory
    so they're easily accessible to Mimic staff.
    We randomize the filename, default permissions are 644,
    and there is no PHP or equiv on this server,
    but be aware other security issues. Note that lighttpd has an x-sendfile module,
    so that you could store the file somewhere non-public and deliver it to Mimic staff that way.
    """
    filename = sanitize_filename(f.name)
    path = 'uploads/%s' % filename
    folder_path = settings.MEDIA_ROOT
    if not os.path.isdir(folder_path + 'uploads'):
        os.mkdir(folder_path + 'uploads')
    destination = open('{0}{1}'.format(folder_path.encode('utf8'), path), 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    url = '%s%s' % (settings.MEDIA_URL, path)
    return url


def sanitize_filename(name):
    """
    Given a filename string:
        * Adds a 4-letter random string at the beginning. 
          This in theory makes the file harder to find for a malicious user,
          but also allows legit users to upload a file more than once
          (eg perhaps revisions) without overwriting it each time.
        * Replaces any non-alphanumeric character with an underscore.
          (Note that there is the regexp shortcut '\W'
          for non-alphanumeric characters, but that also includes periods
          which we want to keep for filenames.) This makes for clean,
          clickable URLs for some email clients (which would
          eg choke on a filename with spaces).
    """
    rstr = ''
    chars = random.sample(['B','C','D','F','G','H','J','K','L','M','N','P','Q','R','S','T','V','W','X','Z'], 4) 
    for c in chars: rstr += c
    r = re.compile('[^a-zA-Z0-9_.]')
    filename = r.sub('_', name)
    return '%s-%s' % (rstr, filename)