from django import template
import re
register = template.Library()

@register.filter()
def qty_list(value, cl=''):
    """
    Given a string of fixed ordering quantities like "100,250,500",
    returns a list of the items, so that it is possible 
    to iterate through them in a template.

    Spaces are stripped out, but the values must be separated by commas.
    """
    value = re.sub(r'[^0-9,]', '', value).split(',')
    return value


@register.filter()
def cifq(x):
    return '"%s"' % unicode(x).replace('"', '""')


@register.filter()
def strftime(v, format):
    return v.strftime(format)


@register.filter()
def product_url(v):
    return "http://mimicprint2.com/oos"


WORD_CHOP = re.compile(r'\s+\S*$')


@register.filter()
def truncatechars(v, max, words=False):
    if len(v) <= max:
        return v

    if words:
        return WORD_CHOP.sub('', v[:max])

    return v[:max]

CLEANER = re.compile(r'^[\s-]+')


@register.filter()
def clear_name(p):
    pname = p.name

    if pname.startswith(p.part_number):
        pname = CLEANER.sub('', pname[len(p.part_number):])

    return pname.strip()
