from django.shortcuts import render_to_response
from django.template import RequestContext

def current_org_required(f):
    """
        Ensures a current_org session variable is set for views which require it.
        Note that this does not redirect to a different view; the requested URL stays the same,
        but the error template is rendered instead.
        This allows the user to select an org and remain on the same page.
    """
    def wrap(request, *args, **kwargs):
        if 'current_org' not in request.session.keys() or not request.session['current_org']:
            request.user.message_set.create(
                message="e|An active organization must be set to view this page."
                )
            return render_to_response('no_current_org.html',
                                      {}, context_instance=RequestContext(request)
                                     )
        return f(request, *args, **kwargs)
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap
