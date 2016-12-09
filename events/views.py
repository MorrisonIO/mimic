from django.http import HttpResponseRedirect, Http404, HttpResponseForbidden
from django.shortcuts import render_to_response, get_object_or_404
from django import forms
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.core.urlresolvers import reverse
from mimicprint.orgs.models import Org
from mimicprint.events.models import Entry
from mimicprint.decorators import current_org_required
from mimicprint.helpers.views import get_query

@login_required
@current_org_required
def client_events_index(request):
    """
    Shows the Events for a particular client. Available only to managers of that Org.
    """
    if request.user.has_perm('reports.change_report'): # manager test
        org = request.session['current_org']
        org_entries = Entry.objects.filter(org=org, status__exact='client')
    else:
        org_entries = None

    return render_to_response('events/client_entry_list.html', {
        'org_entries': org_entries, 
        'public_entries': Entry.objects.public()
    }, context_instance=RequestContext(request))


@login_required
@current_org_required
def client_events_detail(request, slug):
    """
    Shows the detail view for a particular Entry.
    """
    if request.user.has_perm('reports.change_report'): # manager test
        org = request.session['current_org']
        try:
            entry = Entry.objects.get(org=org, slug=slug, status__exact='client')
        except Entry.DoesNotExist:
            entry = get_object_or_404(Entry, slug=slug, status__exact='public')
    else:
        entry = get_object_or_404(Entry, slug=slug, status__exact='public')

    return render_to_response('events/client_entry_detail.html', {
        'entry': entry,
    }, context_instance=RequestContext(request))


def search(request):
    query_string, found_entries = '', ''
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q']
        entry_query = get_query(query_string, ['title', 'body', 'invoice', 'docket'])
        found_entries = Entry.objects.filter(entry_query).filter(org=request.session['current_org']).order_by('-date_created')

    return render_to_response('events/client_entry_list.html', { 
        'search': True,
        'query_string': query_string, 
        'found_entries': found_entries 
    }, context_instance=RequestContext(request))
