from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, Http404, HttpResponseServerError
from django.contrib.auth.decorators import login_required
from django.template import RequestContext, loader, Context
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.core.mail import mail_admins
from django.contrib.auth.forms import SetPasswordForm
from django.conf import settings
from django.db.models import Q
from mimicprint.orders.models import Order
from mimicprint.orgs.models import UserProfile, Org
from mimicprint.events.models import Entry
from mimicprint.downloads.models import Download
from mimicprint.forms import ProfileForm
from mimicprint.orders.views import delete_order_session_vars
import re


@login_required
def dashboard(request):
    """
    The main ordering system homepage (aka the dashboard) to display the user's recent activity, current org info, etc.
    """
    current_org = request.session['current_org'] if 'current_org' in request.session.keys() else '' # requires python 2.5
    entries_list = Entry.objects.filter(status__exact='public')
    if current_org:
        if request.user.has_perm('orders.change_order'):
            order_list = Order.objects.filter(org=current_org)[:5]
            entries_list = Entry.objects.filter(org=current_org, status__exact='client').order_by('-date_created')[:5]
        else:
            order_list = Order.objects.filter(placed_by__exact=request.user)[:5]
        downloads = Download.objects.filter(org=current_org).order_by('-date_added')[:5]
    else: 
        order_list, downloads = None, None

    return render_to_response( 'dashboard.html', { 
        'current_org': current_org,
        'order_list': order_list,
        'entries_list': entries_list,
        'downloads': downloads,
    }, context_instance=RequestContext(request))


@login_required
def setorg(request):
    """
    Sets a session variable for the current 'active' organization. One Organization must be active at all times so that we can show the correct set of products, orders, etc. If a user only belongs to one Organization, this is set automatically; otherwise the user must manually select the active organization. We arrive at this view immediately after login, or when a user manually selects from a menu.
    """
    delete_order_session_vars(request)
    if request.POST.get('org_id', ''): # user changing manually
        org_id = request.POST.get('org_id', '')
        org = Org.objects.get(pk=org_id)
        request.session['current_org'] = org
        return HttpResponseRedirect(request.META['HTTP_REFERER'])
    else: # just logged in
        request.session['current_org'] = ''
        profiles = UserProfile.objects.filter(user=request.user)
        if not profiles.count(): # admin forgot to create a UserProfile
            t = loader.get_template('emails/no_userprofile.txt')
            c = Context({ 'user': request.user })
            mail_admins("[Mimic OOS] Alert! Missing user profile", t.render(c), fail_silently=False)
            t = loader.get_template('500.html')
            c = Context({})
            return HttpResponseServerError(t.render(c))
        else:
            if profiles.count() == 1:
                org = Org.objects.get(pk=profiles[0].org_id)
                request.session['current_org'] = org
        return HttpResponseRedirect(reverse('dashboard'))

@login_required
def logout_user(request):
    """
    Logs out the user to domain-specific page
    """

    from django.contrib.auth.views import logout

    next_page = None
    if 'HTTP_X_FORWARDED_HOST' in request.META and 'podrexall' in request.META['HTTP_X_FORWARDED_HOST']:
        next_page = 'http://www.podrexall.com/loggedout.html'

    return logout(request, next_page)

@login_required
def profile(request):
    """
    Shows a user's profile page, where they can set various options on their account. 
    """
    password_form = SetPasswordForm(request.user)
    profile_form = ''
    current_org = request.session['current_org'] if 'current_org' in request.session.keys() else ''
    if current_org:
        profile = UserProfile.objects.get(user=request.user, org=current_org)
        profile_form = ProfileForm(instance=profile)
    if request.method == 'POST': 
        if 'password' in request.POST: # changing password
            password_form = SetPasswordForm(request.user, request.POST)
            if password_form.is_valid():
                password_form.save()
                request.user.message_set.create(message="s|Your password was successfully changed.")
                return HttpResponseRedirect(reverse('profile'))
            else:
                request.user.message_set.create(message="e|There was a problem with your submission. Refer to the messages below and try again.")

        elif 'profile' in request.POST: # changing prefs
            profile_form = ProfileForm(request.POST, instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                request.user.message_set.create(message="s|Your profile was successfully saved.")
                
    return render_to_response( 'profile.html', { 
        'password_form': password_form,
        'profile_form': profile_form,
        'current_org': current_org
    }, context_instance=RequestContext(request))
