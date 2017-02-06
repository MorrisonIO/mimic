from django import forms
from django.forms import ModelForm
from models import PersonalInfo
class BrochuresPDFForm(forms.Form):
    """
    Class to create PDF from user's files
    """
    pass
    # report_name = forms.CharField()
    # file1 = forms.FileField()
    # file2 = forms.FileField()


class PersonalInfoForm(ModelForm):
    """
    Personal Info model
    """
    class Meta:
        model = PersonalInfo
        fields = '__all__'
