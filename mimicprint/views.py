from django.shortcuts import render #get_object_or_404,
# from django.contrib.auth.decorators import login_required
# from django.contrib.auth.forms import SetPasswordForm
# from django.template import RequestContext, loader, Context
# from orgs.models import UserProfile
# from forms import ProfileForm


def page(request):
    """    Render test page    """
    return render(request, 'page.html', {})

# @login_required
# def profile(request):
#     """
#     Shows a user's profile page, where they can set various options on their account. 
#     """
#     password_form = SetPasswordForm(request.user)
#     profile_form = ''
#     current_org = request.session['current_org'] if 'current_org' in request.session.keys() else ''
#     if current_org:
#         profile = UserProfile.objects.get(user=request.user, org=current_org)
#         profile_form = ProfileForm(instance=profile)
#     if request.method == 'POST': 
#         if 'password' in request.POST: # changing password
#             password_form = SetPasswordForm(request.user, request.POST)
#             if password_form.is_valid():
#                 password_form.save()
#                 request.user.message_set.create(message="s|Your password was successfully changed.")
#                 return HttpResponseRedirect(reverse('profile'))
#             else:
#                 request.user.message_set.create(message="e|There was a problem with your submission. Refer to the messages below and try again.")

#         elif 'profile' in request.POST: # changing prefs
#             profile_form = ProfileForm(request.POST, instance=profile)
#             if profile_form.is_valid():
#                 profile_form.save()
#                 request.user.message_set.create(message="s|Your profile was successfully saved.")
                
#     return render_to_response( 'profile.html', { 
#         'password_form': password_form,
#         'profile_form': profile_form,
#         'current_org': current_org
#     }, context_instance=RequestContext(request))