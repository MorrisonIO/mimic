from django import template
from orgs.models import Org
register = template.Library()

@register.inclusion_tag('templatetags/header_nav.html')
def make_header_nav(user, current_org):
    """
    Makes the org dropdown menu so a user can select the current org in use.
    """

    if user and user.id is not None:
        orgs = Org.objects.filter(userprofile__user=user).order_by('name') 
    else:
        orgs = []

    return { 
        'user': user,
        'orgs': orgs,
        'current_org': current_org
    }
