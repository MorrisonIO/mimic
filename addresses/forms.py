from django import forms
from django.forms import widgets, ModelForm
from mimicprint.addresses.models import Address
from django.forms.util import ErrorList

class AddressForm(ModelForm):
    class Meta:
        model = Address
        exclude = ('owners',)

    def clean(self):
        # If this is not a residential address, a company name is
        # required. See the Django docs about custom validation and
        # attaching error msgs to specific fields:
        # http://docs.djangoproject.com/en/dev/ref/forms/validation/#described-later
        cleaned_data = self.cleaned_data
        is_residential = cleaned_data['is_residential']
        company = cleaned_data['company']
        if not is_residential and not company:
            msg = u"If this is not a residential address, the company field is required."
            self._errors['is_residential'] = ErrorList([msg])
            self._errors['company'] = ErrorList([msg])

            # both fields no longer valid
            del cleaned_data['is_residential']
            del cleaned_data['company']

        # return all cleaned data
        return cleaned_data
