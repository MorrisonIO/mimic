from django.http import HttpResponseRedirect, HttpResponseForbidden, HttpResponse, Http404, HttpResponseServerError
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext, loader, Context
from django import forms
from django.forms import widgets, extras
from django.core.paginator import Paginator, InvalidPage
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib import messages
from reports.models import Report
from reports.forms import ReportForm
from orgs.models import Org, UserProfile
from products.models import Category, Product
from orders.models import Order, OrderedItem
import datetime
from helpers.reporter import ReportFormatter
from dateutil.relativedelta import relativedelta

@login_required
@permission_required('reports.change_report')
def report_list(request):
    """
    Shows the list of reports that a manager has saved.
    """
    reports = Report.objects.filter(owner__exact=request.user.id, is_visible__exact=True)
    return render(request, 'reports/report_list.html', {
        'reports': reports,
    })

@login_required
@permission_required('reports.change_report')
def show_report(request, report_id, download=None, page=None):
    """
    Shows the result of an individual report -- this runs the database query and displays the matching orders.
    """
    report = get_object_or_404(Report, pk=report_id, owner=request.user)
    # Now set up constraints to filter the Orders based on the report's
    # saved options.
    # Filter by date range:

    all_orders = report.orders(download, request.user)

    if download:
        reporter = make_report(all_orders)
        response = HttpResponse(reporter.save(None), mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="%s.xlsx"' % (str(report),) # force save as dialog
        return response

    p = Paginator(all_orders, 20)
    try:
        if page:
            this_page = int(page.replace('page',''))
        else:
            this_page = 1
        page = p.page(this_page)
    except InvalidPage:
        raise Http404

    return render(request, 'reports/report_view.html', {
        'report': report,
        'page': this_page,
        'is_paginated': p.num_pages > 1,
        'has_next': page.has_next(),
        'has_previous': page.has_previous(),
        'next_page': this_page + 1,
        'previous_page': this_page - 1,
        'total_pages': p.num_pages,
        'start_date': str(report.current_start_date).split(' ')[0], # don't need to show user the time part
        'end_date': str(report.current_end_date).split(' ')[0],
        'orders': page.object_list,
        'orgs': report.reported_orgs,
        'prods': report.reported_prods,
        'userprofiles': report.reported_userprofiles,
        'categories': report.reported_categories,
        'num_orders': all_orders.count(),
    })

def make_report(orders):
    """
    Fills ReportFormatter with given orders data.
    """

    reporter = ReportFormatter()

    prev_org = None
    order_count = 0

    for order in orders:
        items = OrderedItem.objects.filter(order=order)
        if not len(items):
            continue

        order_count += 1

        if prev_org != order.org_id:
            if prev_org is not None:
                reporter.section_end()
            prev_org = order.org_id
            reporter.section(str(order.org))

        reporter.order(order)
        reporter.items(items)

    if order_count:
        reporter.section_end()
        reporter.grand_total()

    return reporter

@login_required
@permission_required('reports.change_report')
def delete(request, report_id):
    """
    Deletes a report.
    """
    report = get_object_or_404(Report, pk=report_id, owner=request.user.id)
    if request.method == "POST":
        report.delete()
        messages.success(request, "s|The report was successfully deleted.")
        return HttpResponseRedirect(reverse('report_index'))
    else:
        return render(request, 'reports/delete_confirm.html', {
            'report': report,
        })


@login_required
@permission_required('reports.change_report')
def add_or_edit(request, report_id=None):
    """
    Shows the form for adding or editing a report. Validates and saves data when necessary.
    """
    if report_id:
        report = Report.objects.get(id=report_id, owner=request.user)
        oname = report.name
        daterange_type = report.daterange_type
        form = ReportForm(instance=report, request=request)
    else:
        report = ''
        oname = ''
        daterange_type = ''
        form = ReportForm(request=request)

    if request.method == 'POST':
        if report:
            form = ReportForm(data=request.POST, instance=report, request=request)
        else:
            form = ReportForm(data=request.POST, request=request)

        if form.is_valid():
            new_report = form.save(commit=False)
            new_report.owner_id = request.user.id
            new_report.name = form.cleaned_data['name'] or 'Untitled'

            if request.POST.get('save_report', None):
                new_report.is_visible = True
                messages.success(request, "s|The report was successfully saved.")
                print('report saved')

            force_insert = oname and new_report.name != oname
            if force_insert:
                new_report.pk = None

            new_report.save(force_insert)
            form.save_m2m()
            return HttpResponseRedirect(reverse('report_detail', args=[new_report.id]))
        else:
            messages.warning(request, "e|There was a problem with your submission. Please refer to the messages below and try again.")
            daterange_type = request.POST.get('daterange_type', None)

    return render(request, 'reports/report_edit.html', {
        'report': report,
        'form': form,
        'daterange_type': daterange_type, # we must pass this in separately because we've broken that form field up manually
        'user_can_schedule': request.user.groups.filter(name='Mimic Staff').count() > 0
    })
