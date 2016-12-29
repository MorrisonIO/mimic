from django.shortcuts import render
from django.template import RequestContext
from django.contrib import messages


def current_org_required(f):
    """
        Ensures a current_org session variable is set for views which require it.
        Note that this does not redirect to a different view; the requested URL stays the same,
        but the error template is rendered instead.
        This allows the user to select an org and remain on the same page.
    """
    def wrap(request, *args, **kwargs):
        if 'current_org' not in request.session.keys() or not request.session['current_org']:
            messages.error(request, "e|An active organization must be set to view this page.")
            return render(request, 'no_current_org.html', {})
        return f(request, *args, **kwargs)
    wrap.__doc__ = f.__doc__
    wrap.__name__ = f.__name__
    return wrap
