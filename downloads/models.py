from django.db import models
from django.db.models import permalink
from orgs.models import Org

class Download(models.Model):
    """
        A Download is a file that we place on the site
        that becomes available for the client to log in and get.
        Typically used to deliver proofs instead of making them visit an FTP site.
    """
    name = models.CharField(max_length=200)
    file = models.FileField(upload_to='downloads/files')
    org = models.ForeignKey(Org, blank=True, null=True)
    comments = models.TextField(blank=True, help_text="HTML is allowed.")
    is_deletable = models.BooleanField(
        help_text="If checked, users are allowed to delete this file."
        )
    date_added = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s' % self.name

    @permalink
    def get_absolute_url(self):
        return ('download_detail', None, {'download_id': self.id})

    class Meta:
        ordering = ['name']
