import base64

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.forms import widgets, ModelForm
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext


from helpers.views import get_query
from .forms import AddressForm
from .models import Address


@login_required
def index(request):
    """
    Shows the main list of addresses.
    """
    address_list = Address.objects.filter(owners__in=[request.user]).order_by('last_name')
    paginator = Paginator(address_list, 10) # 10 addresses per page

    # ensure page requested is an int; otherwise show pg 1
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1

    try:
        addresses = paginator.page(page)
    except (EmptyPage, InvalidPage): # if pg # is out of range, show last page
        addresses = paginator.page(paginator.num_pages)

    return render(request, 'addresses/address_list.html', {
        'addresses': addresses,
    })


@login_required
def detail(request, address_id):
    """
    Shows an individual address.
    """
    address = get_object_or_404(Address, pk=address_id, owners__in=[request.user])
    return render(request, 'addresses/address_detail.html', {
        'address': address,
    })


@login_required
def delete(request, address_id):
    """
    Deletes an address. Note that the address is not actually deleted from the
    database, as this might affect the historical accuracy of ship-to addresses
    for orders.
    """
    address = get_object_or_404(Address, pk=address_id, owners__in=[request.user])
    if request.method == 'POST':
        address.owners.remove(request.user)
        address.save()
        t_str = '%s%s-%s' % (request.user.username, request.user.id, address.id)
        token = base64.b64encode(t_str)
        messages.success(request, 's|The address was successfully deleted.\
        <a href="%s" title="Restore address back to your Address Book">Undo</a>'\
         % reverse('address_undo_delete', args=[token]))
        return HttpResponseRedirect(reverse('addresses:address_index'))
    else:
        return render(request, 'addresses/delete_confirm.html', {
            'address': address,
        })


@login_required
def undo_delete(request, token):
    """
    Reassigns an owner back to an address, allowing the user to undelete an
    address.
    """
    try:
        address_id = base64.b64decode(token).split("-")[1]
    except TypeError:
        address_id = 0
    address = get_object_or_404(Address, pk=address_id)
    address.owners.add(request.user)
    address.save()
    messages.success(request ,'s|The address was successfully restored.')
    return HttpResponseRedirect(reverse('addresses:address_index'))


@login_required
def add_or_edit(request, address_id=None, duplicate=None):
    """
    Add, edit, or duplicate an address.
    """
    if duplicate:
        address = get_object_or_404(Address, pk=address_id, owners__in=[request.user])
        address.pk = None
        address.save()
        address.owners.add(request.user)
        address.save()
        messages.success(request, "s|The address was successfully duplicated.\
        Edit your new address below.")
        return HttpResponseRedirect(reverse('addresses:address_edit', args=[address.id]))

    if address_id:
        address = Address.objects.get(id=address_id, owners__in=[request.user])
        address_form = AddressForm(instance=address)
    else:
        address = ''
        address_form = AddressForm()

    if request.method == 'POST':
        if address:
            form = AddressForm(request.POST, instance=address)
        else:
            form = AddressForm(request.POST)
        if form.is_valid():
            new_addr = form.save()
            new_addr.owners.add(request.user)
            new_addr.save()
            messages.success(request, "s|The address was successfully saved.")
            return HttpResponseRedirect(reverse('addresses:address_index'))
        else:
            messages.warning(request, "e|There was a problem with your submission.\
            Refer to the messages below and try again.")
    else:
        form = address_form

    return render(request, 'addresses/address_edit.html', {
        'form': form,
        'address': address,
    })


def search(request):
    """ Search function """
    query_string, found_addresses = '', ''
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        address_query = get_query(query_string, ['first_name', 'last_name', 'company'])
        found_addresses = Address.objects.filter(address_query).filter(owners__in=[request.user]).order_by('-last_name')

    return render(request, 'addresses/address_list.html', {
        'search': True,
        'query_string': query_string,
        'found_addresses': found_addresses
    })
