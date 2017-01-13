from django import forms
from django.forms import widgets

from orgs.models import UserProfile
from products.models import Product, Category


class ProductChartForm(forms.Form):
    """
    Form for creating a chart depicting the amount of product ordered,
    for a set of a particular product(s) over time.
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
        for profile in profiles:
            cats = Category.objects.filter(org=profile.org)
            prods = Product.objects.filter(categories__in=cats)
            for p in prods:
                name_str = '%s [%s]' % (p.name, profile.org)
                prod_choices.append((p.id, name_str))
        self.fields['products'].choices = prod_choices

    products = forms.MultipleChoiceField(choices=(),
                                         required=True,
                                         widget=widgets.SelectMultiple(attrs={'size': '20'})
                                        )


class OrgChartForm(forms.Form):
    """
    Form for creating a chart depicting the amount of a single product ordered,
    for comparing multiple orgs, over time.
    """
    def __init__(self, data=None, request=None, *args, **kwargs):
        if request is None:
            raise TypeError("Keyword argument 'request' must be supplied.")
        super(OrgChartForm, self).__init__(data, *args, **kwargs)
        self.request = request
        profiles = UserProfile.objects.filter(user__exact=request.user)

        prod_choices, org_choices = [], []
        for profile in profiles:
            cats = Category.objects.filter(org=profile.org)
            org_choices.append((profile.org.id, profile.org))
            prods = Product.objects.filter(categories__in=cats)
            for p in prods:
                name_str = '%s [%s]' % (p.name, profile.org)
                prod_choices.append((p.id, name_str))
        self.fields['product'].choices = prod_choices
        self.fields['orgs'].choices = org_choices

    product = forms.ChoiceField(choices=(), required=True)
    orgs = forms.MultipleChoiceField(choices=(),
                                     required=True,
                                     widget=widgets.SelectMultiple(attrs={'size': '20'})
                                    )


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
        orgs = [profile.org for profile in profiles]
        # no staff, otherwise user's chart could include InventoryHistory events
        # which are mimic internal adjustments
        other_users = UserProfile.objects.filter(org__in=orgs, user__is_staff=False)

        prod_choices, user_choices = [], []
        for profile in other_users:
            # make unique user list
            if (profile.user.id, profile.user.get_full_name()) not in user_choices:
                user_choices.append((profile.user.id, profile.user.get_full_name()))
        for org in orgs:
            cats = Category.objects.filter(org=org)
            prods = Product.objects.filter(categories__in=cats)
            for product in prods:
                name_str = '%s [%s]' % (product.name, org)
                prod_choices.append((product.id, name_str))
        self.fields['product'].choices = prod_choices
        self.fields['users'].choices = user_choices

    product = forms.ChoiceField(choices=(), required=True)
    users = forms.MultipleChoiceField(choices=(),
                                      required=True,
                                      widget=widgets.SelectMultiple(attrs={'size': '20'})
                                     )
