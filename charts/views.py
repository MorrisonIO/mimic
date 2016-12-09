from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse, Http404, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext, loader, Context
from django import forms
from django.forms import widgets, extras
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from mimicprint.reports.models import Report
from mimicprint.products.models import Category, Product
from mimicprint.orders.models import Order, OrderedItem
from mimicprint.charts.forms import *
import datetime
from dateutil.relativedelta import relativedelta


@login_required
def index(request):
    """
    Shows the main charts home page, where the user selects which type of chart to create.
    """
    return render_to_response('charts/chart_index.html', {
    }, context_instance=RequestContext(request))


def datetime_to_ms(dt):
    from time import mktime
    return 1000*mktime(dt.timetuple())
    

def assemble_data_string(ordered_items, item):
    """
    Assembles a data string for passing to flot. `ordered_items` is a queryset of OrderedItems filtered according to which chart the user is building. `item` is either a Product, User or Org. 
    """
    start_date = datetime.datetime(2007, 10, 1, 0, 0, 0) # Oct 2007 is when OOS went online
    end_date = datetime.datetime.now()
    delta = relativedelta(months=+1)
    date_counter = start_date
    data_points = ''

    while date_counter <= end_date:
        total_ordered = 0
        this_months_items = ordered_items.filter(inventory_history__date__month=date_counter.month, inventory_history__date__year=date_counter.year)
        for i in this_months_items:
            total_ordered += i.inventory_history.amount
        month_total = '[ %s, %s ], ' % (datetime_to_ms(date_counter), total_ordered) 
        data_points += month_total
        date_counter += delta
    try:
        label = item.get_full_name() # use full name for users
    except AttributeError:
        label = item
    prod_string = """ "%s": { label: "%s", data: [ %s ] }, """ % (label, label, data_points[:-2]) # strip off last comma for IE

    return prod_string


@login_required
def make_chart(request, chart):
    """
    This view displays the appropriate form for creating a chart, and then compiles a data string to pass back to the template, which is rendered with flot.

    Flot needs its data string in the format:
        var datasets = { 
            "foo": { 
                label: "Foo Manual", 
                data: [[ 123, 9 ], [ 150, 3 ]]
            },
            "bar": { 
                label: "Bar Document", 
                data: [[ 149, 19 ], [ 130, 8 ]]
            }
        }; 
    """
    data, data_string = '', ''
    if request.method == 'POST':
        if chart == 'products':
            form = ProductChartForm(request.POST, request=request)
        elif chart == 'users':
            form = UserChartForm(request.POST, request=request)
        else: # orgs
            form = OrgChartForm(request.POST, request=request)

        if form.is_valid():
            if chart == 'products':
                for p in form.cleaned_data['products']:
                    product = Product.objects.get(pk=p)
                    ordered_items = OrderedItem.objects.filter(inventory_history__product=product) 
                    data_string += assemble_data_string(ordered_items, product)
            elif chart == 'users':
                product = Product.objects.get(pk=form.cleaned_data['product'])
                for u in form.cleaned_data['users']:
                    user = User.objects.get(pk=u)
                    ordered_items = OrderedItem.objects.filter(inventory_history__product=product, inventory_history__order__placed_by=user) 
                    data_string += assemble_data_string(ordered_items, user)
            else: # orgs
                product = Product.objects.get(pk=form.cleaned_data['product'])
                for o in form.cleaned_data['orgs']:
                    org = Org.objects.get(pk=o)
                    ordered_items = OrderedItem.objects.filter(inventory_history__product=product, inventory_history__order__org=org) 
                    data_string += assemble_data_string(ordered_items, org)
            data = "{" + data_string[:-2] + "}" # strip off last comma for IE

        else:
            request.user.message_set.create(message="e|There was a problem with your submission. Refer to the messages below and try again.")
    else:
        if chart == 'products':
            form = ProductChartForm(request=request)
        elif chart == 'users':
            form = UserChartForm(request=request)
        else: # orgs
            form = OrgChartForm(request=request)

    return render_to_response('charts/chart_detail.html', {
        'form': form,
        'data': data,
        'chart': chart,
    }, context_instance=RequestContext(request))
