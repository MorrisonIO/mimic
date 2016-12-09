from django import forms
from django.forms import widgets, ModelForm
from mimicprint.orgs.models import UserProfile
from contact_form.forms import ContactForm


class ProfileForm(ModelForm):
    """
    A form to handle a user's profile.
    """
    class Meta:
        model = UserProfile
        exclude = (
            'user', 
            'org', 
            'ignore_pa',
            'unrestricted_qtys',
            'can_see_prices',
        )


class FeedbackForm(ContactForm):
    """
    A form to allow a user to provide feedback.
    """
    TYPE_CHOICES = (
        ('', '--------'),
        ('I have a feature request', 'I have a feature request'),
        ('I think I found a bug', 'I think I found a bug'),
        ('I want to share a success story', 'I want to share a success story'),
        ('I have a general comment', 'I have a general comment')
    )
    feedback_type = forms.ChoiceField(choices=TYPE_CHOICES, required=False)
    name = forms.CharField(max_length=100, widget=widgets.HiddenInput(), required=False)
    email = forms.CharField(max_length=100, widget=widgets.HiddenInput(), required=False)
    body = forms.CharField(widget=forms.Textarea(), label=u'Your message', required=False)
