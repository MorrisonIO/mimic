import datetime
import re

from django import forms

class ProductsPDFForm(forms.Form):
    """
    Class to create PDF from user's files
    """
    title = forms.CharField(max_length=50)
    file1 = forms.FileField()
    file2 = forms.FileField()


