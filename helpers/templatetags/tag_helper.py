""" 
This will return the filename with the cachebuster apppended 

Useage::
    {% js_tag 'test.js' %}
        or 
    {% js_tag 'test' %}

Returns::
    test.js?188a8a2c905fac2670ec4b254d40dadcc7f93f7a

    Author: Greg Newman > greg@20seven.org
"""
from django import template
from django.conf import settings
import hashlib
import time
import datetime
import os
from distutils.dir_util import mkpath

register = template.Library()

def _cleanfilename(filename):
    
    return os.path.splitext(filename)[0]

def _getfiletime(filename):
    basedir = "%s/" % (settings.MEDIA_ROOT)
    if os.path.exists(basedir + "/" + filename):
        return os.path.getmtime(basedir + "/" + filename)
    else:
        return ""

def _hashit(filename):
    cb = hashlib.sha1()
    cb.update(_cleanfilename(filename))
    cb.update(str(_getfiletime(filename)))
    
    return str(cb.hexdigest())

def js_tag(filename):
    tag = "<script src=\"%s%s\" type=\"text/javascript\"></script>" % (settings.STATIC_URL, _cleanfilename(filename) + ".js?" + _hashit(filename))
    
    return tag 


@register.simple_tag
def css_tag(filename):
    tag = "%s" % (_cleanfilename(filename) + ".css?" + _hashit(filename))
    return tag

register.simple_tag(js_tag)
register.simple_tag(css_tag)


@register.filter(name='times')
def times(number):
    """
    Trasform number to list with len equals number.
    List starts from 1, not from 0.
    Uses for loops
    """
    return range(1, number + 1)


@register.filter
def get_name(img_path):
    """
    Gets image path and returns name with extension
    """
    if not img_path:
        return ''
    return img_path.split('/')[-1]


@register.filter
def to_one_word(text):
    """
    Gets text and returns all words joined by '-'
    Example: for 'One two' returns 'One-two'
    """
    import re
    text = re.sub('([^0-9a-zA-Z ]+|[ ]{2,})', '', text)
    return '_'.join(text.lower().split(' '))


@register.filter
def get_value_by_key(obj, key):
    """
    Get object and return value for key
    """
    return obj.get(key, None)


@register.filter
def price_constructor(price):
    """
    Create css class for side menu
    """
    if price < 10: return 'price_max_10'
    elif price < 50: return 'price_max_50'
    elif price < 100: return 'price_max_100'
    elif price < 500: return 'price_max_500'
    elif price < 1000: return 'price_max_1000'
    else: return 'price_max_1000'

@register.filter
def show_category(menu_data):
    """
    Filter menu_data to show in side mwnu only items with data
    """
    _updated_menu_data = {}
    for category in menu_data:
        if len(menu_data[category]) > 1:
            _updated_menu_data[category] = menu_data[category]
    return _updated_menu_data
