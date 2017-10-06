from django.forms import ModelForm
from django.forms.utils import ErrorList
from .models import Address


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
        pickup = cleaned_data['pickup_in_address']

        if pickup and not company:
            msg = u"If this is not a pickup with a residence address, a company field is required."
            self._errors['company'] = ErrorList([msg])

            # both fields no longer valid
            del cleaned_data['company']
            del cleaned_data['pickup_in_address']
            del cleaned_data['address1']
            del cleaned_data['address2']
            del cleaned_data['address3']
            del cleaned_data['city']
            del cleaned_data['country']
            del cleaned_data['postal_code']
            del cleaned_data['province']
        else:
            if not is_residential and not company:
                msg = u"If this is not a residential address, the company field is required."
                self._errors['is_residential'] = ErrorList([msg])
                self._errors['company'] = ErrorList([msg])

                # three fields no longer valid
                del cleaned_data['is_residential']
                del cleaned_data['company']
                del cleaned_data['pickup_in_address']

        # return all cleaned data
        return cleaned_data
