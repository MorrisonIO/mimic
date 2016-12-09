from django import forms
from django.forms import widgets, ModelForm
from django.contrib.auth.models import User
from mimicprint.orgs.models import Org, UserProfile
from mimicprint.products.models import Product, Category
from mimicprint.orders.models import Order
from mimicprint.reports.models import Report
import re

class ReportForm(forms.ModelForm):
    """
    Custom form for adding/editing reports.
    """
    def __init__(self, request=None, *args, **kwargs):
        if request is None:
            raise TypeError("Keyword argument 'request' must be supplied.")
        super(ReportForm, self).__init__(*args, **kwargs)
        QUARTER_START_CHOICES = (
            ('', '---'),
            ('01', 'January'),
            ('02', 'February'),
            ('03', 'March'),
            ('04', 'April'),
            ('05', 'May'),
            ('06', 'June'),
            ('07', 'July'),
            ('08', 'August'),
            ('09', 'September'),
            ('10', 'October'),
            ('11', 'November'),
            ('12', 'December'),
        )
        self.request = request
        orgs = UserProfile.objects.filter(user__exact=request.user)

        org_choices, prod_choices, user_choices, cats_choices = [], [], [], []
        for o in orgs:
            org_choices.append((o.org.id, o.org))
            users = UserProfile.objects.filter(org=o.org)
            cats = Category.objects.filter(org=o.org)
            prods = Product.objects.filter(categories__in=cats)
            for p in prods:
                prod_choices.append((p.id, p.name))
            for u in users:
                user_choices.append((u.id, "%s [%s]" % (u.user.get_full_name(), o.org)))
            for c in cats:
                cats_choices.append((c.id, "[%d] %s" % (c.id, c.name)))

        self.fields['orgs'].choices = org_choices
        self.fields['products'].choices = prod_choices
        self.fields['ordered_by'].choices = user_choices
        self.fields['categories'].choices = cats_choices
        self.fields['quarter_start'].widget = widgets.Select(choices=QUARTER_START_CHOICES)
        self.fields['start_date'].widget = widgets.TextInput(attrs={'class': 'datepicker', 'size': '12'})
        self.fields['end_date'].widget = widgets.TextInput(attrs={'class': 'datepicker', 'size': '12'})
        self.fields['last_orders'].widget = widgets.TextInput(attrs={'size': '3'})
        self.fields['scheduled'].widget = widgets.CheckboxInput()
        self.fields['schedule'].widget = widgets.HiddenInput()
        self.fields['states'].widget = widgets.SelectMultiple(choices=Order.STATUS_CHOICES)

    def clean_quarter_start(self):
        """
        If viewing a quarterly-based date range, the quarter start date is required.
        """
        if (self.cleaned_data['daterange_type'] == 'tq' or self.cleaned_data['daterange_type'] == 'lq') and not self.cleaned_data['quarter_start']:
            raise forms.ValidationError('Enter when your first fiscal quarter starts.')
        else:
            return self.cleaned_data['quarter_start']

    def clean_last_orders(self):
        """
        If viewing the last n orders, the number of orders is required.
        """
        if self.cleaned_data['daterange_type'] == 'fn' and not self.cleaned_data['last_orders']:
            raise forms.ValidationError('Enter the number of orders to show.')
        else:
            return self.cleaned_data['last_orders']

    def clean_start_date(self):
        """
        If viewing orders between fixed dates, start date is required.
        """
        if self.cleaned_data['daterange_type'] == 'fd' and not self.cleaned_data['start_date']:
            raise forms.ValidationError('Enter the start date.')
        else:
            return self.cleaned_data['start_date']

    def clean_end_date(self):
        """
        If viewing orders between fixed dates, end date is required. End date must also be further ahead in time than start date.
        """
        if self.cleaned_data['daterange_type'] == 'fd' and not self.cleaned_data['end_date']:
            raise forms.ValidationError('Enter the end date.')
        elif self.cleaned_data['daterange_type'] == 'fd' and (self.cleaned_data['end_date'] < self.cleaned_data['start_date']):
            raise forms.ValidationError('End date must be later than start date.')
        else:
            return self.cleaned_data['end_date']

    def clean_schedule(self):
        """
        Check schedule format
        """

        if re.match(r'^((-1|\d{1,2}|\*)\s){4}(-1|\d{1,2}|\*)$', self.cleaned_data['schedule']):
            return self.cleaned_data['schedule']
        else:
            raise forms.ValidationError('Invalid schedule specification')

    def clean_states(self):
        data = [x for x in self.data.getlist('states') if x in Report.DEFAULT_STATES]
        if not data:
            raise forms.ValidationError('States required')
        return data

    class Meta:
        model = Report
        exclude = (
            'owner',
            'is_visible',
            '_states'
        )
