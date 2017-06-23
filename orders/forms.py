import datetime
import re

from django import forms
from django.contrib.auth.models import User
from django.forms import widgets, ModelForm, BaseForm

from orgs.models import Org
from addresses.models import Address
from products.models import Product
from orders.models import Order

class OrderPDFForm(forms.Form):
    """
    Class to create PDF from user's files
    """
    title = forms.CharField(max_length=50)
    file1 = forms.FileField()
    file2 = forms.FileField()


class OrderForm(forms.ModelForm):
    """
    A form to handle the other info needed when ordering apart
    from the products and shipto: due date, additional info, etc.
    """
    upload_file = forms.FileField(required=False)

    def save(self, *args, **kwargs):
        super(OrderForm, self).save(*args, **kwargs)


    def __init__(self, request=None, *args, **kwargs):
        super(OrderForm, self).__init__(*args, **kwargs)
        self.request = request
        self.fields['due_date'].widget = widgets.TextInput(attrs={'class': 'datepicker'})
        self.fields['shipping_date'].widget = widgets.TextInput(attrs={'class': 'datepicker'})
        try:
            due_date = request.session['due_date']
        except KeyError:
            due_date = ''
        try:
            shipping_date = request.session['shipping_date']
        except KeyError:
            shipping_date = ''
        try:
            po_number = request.session['po_number']
        except KeyError:
            po_number = ''
        try:
            additional_info = request.session['additional_info']
        except KeyError:
            additional_info = ''
        try:
            cc_confirmation = request.session['cc_confirmation']
        except KeyError:
            cc_confirmation = ''

        self.fields['due_date'].initial = due_date
        self.fields['po_number'].initial = po_number
        self.fields['additional_info'].initial = additional_info
        self.fields['cc_confirmation'] = forms.CharField(
            label="CC order confirmation to",
            widget=widgets.TextInput,
            required=False,
            help_text="Email addresses of people to copy the order confirmation email to. Separate multiple addresses with commas.",
            initial=cc_confirmation
        )

    class Meta:
        model = Order
        fields = ('po_number', 'due_date', 'shipping_date', 'additional_info', 'upload_file')

    def clean_due_date(self):
        """
        Ensures the due date is in the future.
        """
        if self.cleaned_data['due_date'] < datetime.date.today():
            raise forms.ValidationError("The due date must be in the future.")
        else:
            return self.cleaned_data['due_date']

    def clean_cc_confirmation(self):
        """
        Ensure all email addresses are valid.
        """
        email_re = re.compile( # from django/forms/fields.py
            r"(^[-!#$%&'*+/=?^_`{}|~0-9A-Z]+(\.[-!#$%&'*+/=?^_`{}|~0-9A-Z]+)*"  # dot-atom
            r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-011\013\014\016-\177])*"' # quoted-string
            r')@(?:[A-Z0-9-]+\.)+[A-Z]{2,6}$', re.IGNORECASE)  # domain
        if self.cleaned_data['cc_confirmation']:
            addresses = list(self.cleaned_data['cc_confirmation'].replace(" ", "").split(','))
            for a in addresses:
                if not email_re.search(a):
                    raise forms.ValidationError("You have entered an invalid email address.")
        return self.cleaned_data['cc_confirmation']


class ShipToField(forms.Field):
    def __init__(self, data=None, *args, **kwargs):
        super(ShipToField, self).__init__(data, *args, **kwargs)
        staff = list(User.objects.filter(is_staff=True))
        try:
            addresses = [(a.id, a) for a in Address.objects.filter(owners__in=staff)]
        except Exception as ex:
            print "Error ShipToField: {}".format(ex)
            addresses = []
        self.widget = forms.Select(attrs={'class':'required'}, choices=addresses)
        self.required = True

    def clean(self, value):
        if not value:
            raise forms.ValidationError('Select a ship to address.')
        try:
            address = Address.objects.get(pk=value)
        except:
            raise forms.ValidationError('That address does not exist.')
        return value


class FastOrderForm(forms.Form):
    """
    Form for adding a FastOrder. Data we need to get from user: due_date*, org*,
    ship_to*, po_number, additional_info,products + quantities (at least one required).
    All other fields of the Order model are either not relevant, or can by filled in dynamically.
    """
    org_choices = [('', '---------'),]
    product_choices = [('', '---------'),]
    try:
        org_choices += [(org.id, org.name) for org in Org.objects.all()]
        product_choices += [(prod.id, prod.name) for prod in Product.objects.all()]
    except Exception as ex:
        print "Error FastOrderForm: {}".format(ex)

    org = forms.ChoiceField(required=True, choices=org_choices, widget=forms.Select(attrs={'class': 'required'}))
    due_date = forms.DateField(required=True, widget=forms.TextInput(attrs={'class': 'vDateField required', 'size': '12'}))
    #    ship_to = forms.ChoiceField(required=True, choices=shipto_choices, widget=forms.Select(attrs={'class': 'required'}))
    #    ship_to = forms.ChoiceField(required=True, widget=forms.Select(attrs={'class': 'required'}))
    ship_to = ShipToField()
    po_number = forms.CharField(max_length=50, widget=forms.TextInput(), required=False)
    additional_info = forms.CharField(widget=forms.Textarea(), required=False)
    job1_product = forms.ChoiceField(required=True, choices=product_choices, widget=forms.Select(attrs={'class':'required'}))
    job1_qty = forms.IntegerField(required=True, widget=forms.TextInput(attrs={'size':'5', 'class':'required'}))
    job2_product = forms.ChoiceField(required=False, choices=product_choices, widget=forms.Select())
    job2_qty = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'size':'5'}))
    job3_product = forms.ChoiceField(required=False, choices=product_choices, widget=forms.Select())
    job3_qty = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'size':'5'}))
    job4_product = forms.ChoiceField(required=False, choices=product_choices, widget=forms.Select())
    job4_qty = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'size':'5'}))
    job5_product = forms.ChoiceField(required=False, choices=product_choices, widget=forms.Select())
    job5_qty = forms.IntegerField(required=False, widget=forms.TextInput(attrs={'size':'5'}))

    def clean_job2_qty(self):
        """
        If a product is selected for job 2, we also need a quantity.
        """
        if (self.cleaned_data['job2_product'] and self.cleaned_data['job2_qty'] is None):
            raise forms.ValidationError('Enter a quantity.')
        else:
            return self.cleaned_data['job2_qty']

    def clean_job3_qty(self):
        """
        If a product is selected for job 3, we also need a quantity.
        """
        if (self.cleaned_data['job3_product'] and self.cleaned_data['job3_qty'] is None):
            raise forms.ValidationError('Enter a quantity.')
        else:
            return self.cleaned_data['job3_qty']

    def clean_job4_qty(self):
        """
        If a product is selected for job 4, we also need a quantity.
        """
        if (self.cleaned_data['job4_product'] and self.cleaned_data['job4_qty'] is None):
            raise forms.ValidationError('Enter a quantity.')
        else:
            return self.cleaned_data['job4_qty']

    def clean_job5_qty(self):
        """
        If a product is selected for job 5, we also need a quantity.
        """
        if (self.cleaned_data['job5_product'] and self.cleaned_data['job5_qty'] is None):
            raise forms.ValidationError('Enter a quantity.')
        else:
            return self.cleaned_data['job5_qty']
            