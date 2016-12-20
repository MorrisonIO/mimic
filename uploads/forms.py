from django import forms

class UploadFileForm(forms.Form):
    """
    Form to handle allowing users to upload files.
    """
    CONTACT_CHOICES = (
        ('No', "No, contact is not necessary"),
        ('By phone', "Yes, by phone"),
        ('By email', "Yes, by email"),
    )
    name = forms.CharField(max_length=100, required=False)
    company = forms.CharField(max_length=100, required=False)
    contact_user = forms.ChoiceField(choices=CONTACT_CHOICES, required=False)
    phone = forms.CharField(max_length=20, required=False)
    email = forms.EmailField(required=False)
    title = forms.CharField(max_length=50, required=False)
    comments = forms.CharField(required=False, widget=forms.Textarea())
    file  = forms.FileField()
