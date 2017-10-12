from django.forms import ModelForm
from django.forms.utils import ErrorList
from .models import Address


class AddressForm(ModelForm):
    class Meta:
        model = Address
        exclude = ('owners',)

    def is_valid(self):

        # if there is no value in the list - return: False
        def noEmpty(noEmptyList):
            for fild in noEmptyList:
                if not self.data[fild]:
                    return False
            return True

        noEmptyList1 = ['first_name', 'last_name', 'phone', 'email']
        if not noEmpty(noEmptyList1):
            return False

        # validation for pickup
        try:
            if self.data['pickup_in_address']:
                pass
        except:
            noEmptyList2 = ['address1', 'city', 'country', 'postal_code', 'province']
            if not noEmpty(noEmptyList2):
                return False

        try:
            if self.data['is_residential']:
                pass
        except:
            if not noEmpty(['company']):
                return False

        return True

    def clean(self):
        # If this is not a residential address, a company name is
        # required. See the Django docs about custom validation and
        # attaching error msgs to specific fields:
        # http://docs.djangoproject.com/en/dev/ref/forms/validation/#described-later
        cleaned_data = self.cleaned_data
        is_residential = cleaned_data['is_residential']
        company = cleaned_data['company']
        pickup = cleaned_data['pickup_in_address']

        def delItems(name):
            try:
                if name in cleaned_data:
                    del cleaned_data[name]
            except:
                pass

        if pickup and not company:
            msg = u"If this is not a pickup with a residence address, a company field is required."
            self._errors['company'] = ErrorList([msg])

            # fields no longer valid
            delItems('company')
            delItems('pickup_in_address')
            delItems('address1')
            delItems('address2')
            delItems('address3')
            delItems('city')
            delItems('country')
            delItems('postal_code')
            delItems('province')
        else:
            if not is_residential and not company:
                msg = u"If this is not a residential address, the company field is required."
                self._errors['is_residential'] = ErrorList([msg])
                self._errors['company'] = ErrorList([msg])

                # three fields no longer valid
                delItems('is_residential')
                delItems('company')
                delItems('pickup_in_address')

        # return all cleaned data
        return cleaned_data
