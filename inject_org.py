def inject(request):
    if hasattr(request, 'session') and 'current_org' in request.session.keys():
        current_org = request.session['current_org']
    else:
        current_org = None

    return {
        'user_session_org': current_org,
        'on_podrexall': ('HTTP_X_FORWARDED_HOST' in request.META and 'podrexall' in request.META['HTTP_X_FORWARDED_HOST'])
    }
