from django import template
from orgs.models import Org
register = template.Library()


@register.inclusion_tag('templatetags/order_progress.html')
def show_order_progress(request, page):
    """
    Makes the order progress graphic so the user can gauge progress
    and return to previous ordering pages.
    `page` is a string representing the current page in the ordering process,
    `request` is the Django request object, needed because the template
    that is rendered by this inclusion tag needs access to session variables.
    """
    return {
        'request': request,
        'page': page
    }


@register.inclusion_tag('templatetags/creation_progress.html')
def show_creation_progress(request, page):
    """
    Makes the creation pdf progress graphic so the user can gauge progress
    and return to previous ordering pages.
    `page` is a string representing the current page in the ordering process,
    `request` is the Django request object, needed because the template
    that is rendered by this inclusion tag needs access to session variables.
    """
    return {
        'request': request,
        'page': page
    }
