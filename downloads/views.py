from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django import forms
from django.forms import widgets
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from mimicprint.downloads.models import Download
from mimicprint.decorators import current_org_required

@login_required
@current_org_required
def index(request):
    """
    Shows the main list of files waiting to be downloaded.
    """
    org = request.session['current_org']
    downloads = Download.objects.filter(org=org).order_by("-date_added")
    return render_to_response('downloads/download_list.html', {
        'downloads': downloads, 
    }, context_instance=RequestContext(request))


@login_required
def detail(request, download_id):
    """
    Shows an individual download. (This view is currently only needed for URL resolving/permalinks to work; it is not visited directly, since the link the user clicks on to 'view' the file goes direct to where it is on the media server.)
    """
    return HttpResponseRedirect(reverse('download_index'))


@login_required
@current_org_required
def delete(request, download_id):
    """
    Deletes a file. This merely unassigns which Org this Download belongs to; thus it no longer appears to the user, but it can be undeleted. 
    """
    org = request.session['current_org']
    download = get_object_or_404(Download, pk=download_id, org=org) 
    if request.method == 'POST':
        if download.is_deletable:
            download.org_id = 0 
            download.save()
            request.user.message_set.create(message='s|The file was successfully deleted. <a href="%s" title="Restore file back to your Download area">Undo</a>' % reverse('download_undo_delete', args=[download.id]))
        return HttpResponseRedirect(reverse('download_index'))
    else:
        if download.is_deletable:
            return render_to_response('downloads/delete_confirm.html', {
                'download': download,
            }, context_instance=RequestContext(request))
        return HttpResponseRedirect(reverse('download_index'))


@login_required
@current_org_required
def undo_delete(request, download_id):
    """
    Reassigns an owner back to a Download, allowing the user to undelete it.
    """
    org = request.session['current_org']
    download = get_object_or_404(Download, pk=download_id, org=0) 
    download.org = org
    download.save()
    request.user.message_set.create(message='s|The file was successfully restored.')
    return HttpResponseRedirect(reverse('download_index'))
