import datetime
import re

from django import forms

class ProductsPDFForm(forms.Form):
    """
    Class to create PDF from user's files
    """
    report_name = forms.CharField()
    file1 = forms.FileField()
    file2 = forms.FileField()


