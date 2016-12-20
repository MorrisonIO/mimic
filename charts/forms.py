from django import forms
from django.forms import BaseForm
from django.contrib.auth.models import User
from django.forms import widgets
from orgs.models import UserProfile
from products.models import Product, Category

class ProductChartForm(forms.Form):
    """
    Form for creating a chart depicting the amount of product ordered, for a set of a particular product(s) over time. 
    """
    # Add in the dynamic choices which depend on the user.
    # For this chart we need which products to display -- all products
    # which belong to all categories which belong to the orgs the user
    # belongs to.
    def __init__(self, data=None, request=None, *args, **kwargs):
        if request is None:
            raise TypeError("Keyword argument 'request' must be supplied.")
        super(ProductChartForm, self).__init__(data, *args, **kwargs)
        self.request = request
        profiles = UserProfile.objects.filter(user__exact=request.user)

        prod_choices = []
        for up in profiles:
            cats = Category.objects.filter(org=up.org)
            prods = Product.objects.filter(categories__in=cats)
            for p in prods:
                name_str = '%s [%s]' % (p.name, up.org)
                prod_choices.append((p.id, name_str))
        self.fields['products'].choices = prod_choices

    products = forms.MultipleChoiceField(choices=(), required=True, widget=widgets.SelectMultiple(attrs={'size': '20'}))

class OrgChartForm(forms.Form):
    """
    Form for creating a chart depicting the amount of a single product ordered, for comparing multiple orgs, over time. 
    """
    def __init__(self, data=None, request=None, *args, **kwargs):
        if request is None:
            raise TypeError("Keyword argument 'request' must be supplied.")
        super(OrgChartForm, self).__init__(data, *args, **kwargs)
        self.request = request
        profiles = UserProfile.objects.filter(user__exact=request.user)

        prod_choices, org_choices = [], []
        for up in profiles:
            cats = Category.objects.filter(org=up.org)
            org_choices.append((up.org.id, up.org))
            prods = Product.objects.filter(categories__in=cats)
            for p in prods:
                name_str = '%s [%s]' % (p.name, up.org)
                prod_choices.append((p.id, name_str))
        self.fields['product'].choices = prod_choices
        self.fields['orgs'].choices = org_choices

    product = forms.ChoiceField(choices=(), required=True)
    orgs = forms.MultipleChoiceField(choices=(), required=True, widget=widgets.SelectMultiple(attrs={'size': '20'}))

class UserChartForm(forms.Form):
    """
    Form for creating a chart depicting the amount of a single product ordered, for comparing multiple users, over time. 
    """
    def __init__(self, data=None, request=None, *args, **kwargs):
        if request is None:
            raise TypeError("Keyword argument 'request' must be supplied.")
        super(UserChartForm, self).__init__(data, *args, **kwargs)
        self.request = request
        profiles = UserProfile.objects.filter(user__exact=request.user) 
        orgs = [ p.org for p in profiles ]
        other_users = UserProfile.objects.filter(org__in=orgs, user__is_staff=False) # no staff, otherwise user's chart could include InventoryHistory events which are mimic internal adjustments
        
        prod_choices, user_choices = [], []
        for up in other_users:
            if not (up.user.id, up.user.get_full_name()) in user_choices: # make unique user list
                user_choices.append((up.user.id, up.user.get_full_name())) 
        for o in orgs:
            cats = Category.objects.filter(org=o)
            prods = Product.objects.filter(categories__in=cats)
            for p in prods:
                name_str = '%s [%s]' % (p.name, o)
                prod_choices.append((p.id, name_str))
        self.fields['product'].choices = prod_choices
        self.fields['users'].choices = user_choices

    product = forms.ChoiceField(choices=(), required=True)
    users = forms.MultipleChoiceField(choices=(), required=True, widget=widgets.SelectMultiple(attrs={'size': '20'}))
