from django.db import models
from django.db.models import permalink
from django.contrib.auth.models import User


class Address(models.Model):
    """
        A contact or frequently shipped-to location.
        Addresses may be saved as belonging to a particular user,
        in which case they appear in the user's Address Book.
    """
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)
    title = models.CharField(max_length=200, blank=True)
    company = models.CharField(max_length=200, blank=True)
    address1 = models.CharField(max_length=200)
    address2 = models.CharField(max_length=200, blank=True)
    address3 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200)
    province = models.CharField("Province/State", max_length=200)
    postal_code = models.CharField("Postal/Zip code", max_length=20)
    country = models.CharField(max_length=200)
    phone = models.CharField(max_length=50)
    cell = models.CharField(max_length=50, blank=True)
    fax = models.CharField(max_length=50, blank=True)
    email = models.EmailField(max_length=50, blank=True)
    is_residential = models.BooleanField(
        "Is this a residential address?",
        blank=True, help_text="Yes"
        )
    owners = models.ManyToManyField(User, blank=True)

    def __unicode__(self):
        if self.company:
            return u'%s, %s (%s)' % (self.last_name, self.first_name, self.company)
        return u'%s %s' % (self.first_name, self.last_name)

    class Meta:
        verbose_name_plural = 'Addresses'
        ordering = ['last_name']

    @permalink
    def get_absolute_url(self):
        return ('address_detail', None, {'address_id': self.id})
