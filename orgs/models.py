from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

class Org(models.Model):
    """ 
    An Org is an organization of users. This can represent an entire client, a
    division of a client, or any arbitrary collection of users. Each user must
    belong to at least one Org. This class is used instead of the 'group' class
    from django.contrib.auth.
    """
    name = models.CharField(max_length=200)
    homepage_notes = models.TextField(help_text="Use HTML. Include contact info for the appropriate Mimic sales rep.", blank=True)
    logo = models.ImageField(upload_to='logos', blank=True, help_text="JPG or GIF format, 72dpi, white background, maximum 250 pixels wide.")
    logo_icon = models.ImageField(upload_to='logo_icons', blank=True, help_text="JPG or GIF format, 72dpi, transparent background, maximum 173 pixels wide.")
    approval_manager = models.ForeignKey(User, blank=True, null=True, related_name="org_approval_manager_set")
    additional_info_helptext = models.TextField("Ordering additional info instructions", help_text="Provide instructions for the 'additional info' area when placing an order -- notify user of any required information they need to provide.", blank=True)
    mimic_rep = models.ManyToManyField(User, help_text="These people will be notified by email of orders and approvals.", verbose_name="Mimic account rep(s)", limit_choices_to = {'is_staff__exact': '1'})
    client_code = models.CharField(max_length=200, blank=True)
    address1 = models.CharField(max_length=200, blank=True)
    address2 = models.CharField(max_length=200, blank=True)
    address3 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    province = models.CharField("Province/State", max_length=200, blank=True)
    postal_code = models.CharField("Postal/Zip code", max_length=20, blank=True)
    country = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=50, blank=True) 
    fax = models.CharField(max_length=50, blank=True) 
    is_residential = models.BooleanField("Is this a residential address?", blank=True, help_text="Yes")
    notes = models.TextField(help_text="Keep miscellaneous notes here. Not visible to clients.", blank=True)
    order_email = models.CharField("Order email template", max_length=200, blank=True, help_text="Name of custom email template to send when orders are placed. Place in /templates/emails/. Defaults to order_confirmed.txt.")
    approval_email = models.CharField("Approval email template", max_length=200, blank=True, help_text="Name of custom email template to send when orders requiring approval are placed. Place in /templates/emails/. Defaults to order_approvalrequired.txt.")

    def __unicode__(self):
        return u'%s' % self.name

    def get_id(self):
        return self.id

    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ['name']

class UserProfile(models.Model):
    """
    A UserProfile is an extension of the User model that comes with
    django.contrib.auth. It is used primarily to determine which user belongs
    to which organizations.
    """
    # WARNING: If you are adding a field the user should *not* see, you need to manually add it to the excludes list in the ProfileForm class (mimicprint/forms.py)
    PRODUCT_VIEW_CHOICES = (
        ('e', 'Expanded'),
        ('c', 'Collapsed'),
    )
    user = models.ForeignKey(User)
    org = models.ForeignKey(Org)
    bus_phone = models.CharField("Business phone", max_length=100, blank=True)
    cell_phone = models.CharField(max_length=100, blank=True)
    home_phone = models.CharField(max_length=100, blank=True)
    ignore_pa = models.BooleanField("Ignore pending approval", help_text="If checked, any Pending Approval requirements on products will be ignored for this user; orders will placed will have an immediate status of Active.")
    unrestricted_qtys = models.BooleanField("Unrestricted ordering quantities", help_text="If checked, the user will be able to order any amount of a product, and not be limited by minimums or fixed ordering quantities. Managers have unrestricted ordering by default, regardless of this setting.")
    default_product_view = models.CharField(max_length=2, choices=PRODUCT_VIEW_CHOICES, blank=True, help_text="How the categories on the product list page will appear by default.")
    can_see_prices = models.BooleanField("User can see prices", help_text="If checked, this user will see the price of products in the Product List. (Not required for Managers, as managers see prices by default.)")

    def __unicode__(self):
        return u'%s: %s' % (self.user, self.org)

    class Meta:
        ordering = ['user']
