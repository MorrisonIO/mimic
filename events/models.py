from django.db import models
from django.contrib.auth.models import User
from orgs.models import Org
from .managers import ManagerWithPublic

class Entry(models.Model):
    """
        An Entry is one post about how we have saved a client time/money/face, etc.
    """
    STATUS_CHOICES = (
        ('private', 'Private - Mimic only'),
        ('client', 'Viewable to client'),
        ('public', 'Publish on Mimic site'),
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(help_text="Used in the URL for this entry. Auto-populated from title.")
    body = models.TextField(help_text="Enter the main details of the event. Markdown ok.")
    summary = models.TextField(help_text="A summary of the body, to be used on the list page. If blank, the first several words of 'body' will be used.", blank=True)
    org = models.ForeignKey(Org, blank=True, null=True, help_text="If making viewable to client, this must be set.")
    published_by = models.ForeignKey(User, limit_choices_to = {'is_staff__exact': '1'})
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    date = models.DateField(help_text="Date this event took place.")
    docket = models.CharField(max_length=200, help_text="Docket number this pertains to. Not publicly shown.", blank=True)
    invoice = models.CharField(max_length=200, help_text="Invoice number this pertains to. Not publicly shown.", blank=True)
    date_created = models.DateTimeField(auto_now_add=True)
    objects = ManagerWithPublic()

    def __unicode__(self):
        return u'%s' % self.title

    class Meta:
        verbose_name_plural = 'Entries'
        ordering = ['date_created']
