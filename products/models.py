import simplejson as json
from django.db import models
from django.db.models import permalink
from django.conf import settings
from django.contrib.auth.models import User
from orgs.models import Org
import string
import random

#
# NOTE: Many Mimic internal-specific things in this file
#

class Category(models.Model):
    """
    A category is an arbitrary collection of Products (eg. Stationery, Marketing Materials) belonging to one Organization.
    """
    name = models.CharField(max_length=200)
    org = models.ForeignKey(Org)
    name_altname = models.CharField("'Name' column header", max_length=200, blank=True)
    description_altname = models.CharField("'Description' column header", max_length=200, blank=True)
    revision_altname = models.CharField("'Revision' column header", max_length=200, blank=True)
    show_revision = models.BooleanField("Show 'Revision' column", blank=True)
    part_number_altname = models.CharField("'Part Number' column header", max_length=200, blank=True)
    show_part_number = models.BooleanField("Show 'Part Number' column", blank=True)
    price_altname = models.CharField("'Price' column header", max_length=200, blank=True)
    show_price = models.BooleanField("Show 'Price' column", blank=True)
    show_inventory = models.BooleanField("Show 'Inventory' column", blank=True)
    sort = models.IntegerField(max_length=5, blank=True, null=True, help_text="Enter an integer to create an order that categories will be displayed in. Note that other categories will need a value as well.")
    date_added = models.DateField(auto_now_add=True)
    date_modified = models.DateField(auto_now=True)

    def __unicode__(self):
        return u'[%s] %s' % (self.org, self.name) # necessary in admin so we can tell which org a category belongs to (ie if there is >1 "Stationery" category)

    @permalink
    def get_absolute_url(self):
        return ('category_list', None, { 'cat_id': self.id })

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['org', 'name']


class Product(models.Model):
    """
    A product is one item available for ordering.
    """
    STATUS_CHOICES = (
        ('av', 'Available'), # display on client site
        ('in', 'Invisible'), # do not display (both client site and internally for one-offs)
        ('ar', 'Archived'),  # not currently used
    )
    PAPER_CHOICES = (
        ('pure', 'Pure'),
        ('mixed1', 'Mixed 1'),
        ('mixed2', 'Mixed 2'),
        ('mixed3', 'Mixed 3'),
        ('recycled', 'Recycled'),
    )
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=200, blank=True)
    categories = models.ManyToManyField(Category, blank=True)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES, default='av')
    preview = models.ImageField(upload_to='products', blank=True, help_text="JPG format, 72dpi, not larger than 600 pixels wide x 800 pixels tall.")
    revision = models.CharField(max_length=50, blank=True)
    part_number = models.CharField(max_length=50, blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2, blank=True, null=True, help_text="Do not enter a dollar sign.")
    min_order_qty = models.PositiveIntegerField("Minimum order quantity", max_length=10, blank=True, null=True, help_text="Ensure this does not conflict with any fixed quantities below.")
    approval_required = models.BooleanField(blank=True, help_text="A manager must approve an order containing this item before it's placed into production. NOTE: Make sure an approval manager is set for the Organization in question!")
    fixed_order_qtys = models.CharField("Fixed order quantities", max_length=200, blank=True, help_text="Separate quantities with commas; no spaces. Example: 5,10,15,20")
    track_inventory = models.BooleanField(blank=True, help_text="Check to keep a running total of how many of this item we have.")
    inventory = models.IntegerField("Current inventory", blank=True, null=True, help_text="<span style='color: red'>DO NOT EDIT HERE!</span> Add an Inventory History event instead.")
    warehouse_location = models.CharField(max_length=50, blank=True, help_text="Enter the appropriate aisle and shelf numbers.")
    replenish_threshold = models.PositiveIntegerField(max_length=15, blank=True, null=True, help_text="Send an email alert when inventory drops below this amount.")
    is_variable = models.BooleanField("This is a variable data product", blank=True, help_text="Check if this product requires input from the user. Note that you MUST also enter a class name below!")
    var_form = models.CharField("Variable data form/class name", max_length=50, blank=True, help_text="Enter the name of the custom class that creates the form for this product.")
    page_count = models.PositiveIntegerField(max_length=5, blank=True, null=True)
    prepress_info = models.TextField("Prepress information", blank=True)
    bw_info = models.TextField("Docutech information", blank=True)
    colour_info = models.TextField("Colour information", blank=True)
    bindery_info = models.TextField("Bindery information", blank=True)
    shipping_info = models.TextField("Shipping information", blank=True)
    billing_info = models.TextField("Billing information", blank=True)
    outsourcing_info = models.TextField("Outsourcing information", blank=True)
    sort = models.IntegerField(max_length=5, blank=True, null=True, help_text="Enter an integer to create an order that products will be displayed in. Note that other products will need a value as well.")
    is_component = models.BooleanField()
    ratios = models.ManyToManyField('ComponentRatio', blank=True, help_text="If this product has components, select the correct ratios of components used.") # quotes around model name because it isn't defined yet
    is_fsc = models.BooleanField(verbose_name="This is an FSC certified product")
    paper_type = models.CharField(max_length=20, choices=PAPER_CHOICES, blank=True)
    logo_position = models.CharField(max_length=100, blank=True)
    smartwood_proof = models.BooleanField()
    date_added = models.DateField(auto_now_add=True)
    date_modified = models.DateField(auto_now=True)

    def __unicode__(self):
        return u'%s' % self.name

    class Meta:
        ordering = ['name']

    def in_categories(self):
        """
        Used in the admin on the change list page, to show which categories each product is in. NOTE: Will probably slow the page down due to excessive DB querying.
        """
        cats = ''
        for c in self.categories.all():
            cats += '%s, ' % c
        return cats[:-2]

    def unique_id(self):
        """
        Returns a random 7 digit string, for use in uniquely identifying variable data items.
        """
        uid = ''
        nums = random.sample(range(0,9), 7)
        for n in nums: uid += str(n)
        return uid

class ProductSelection(models.Model):
    product = models.ForeignKey(Product)

    def __unicode__(self):
        return u'[%s] %s (%d)' % (
            self.product.part_number,
            self.product.name,
            self.product.id
        )

class ComponentRatio(models.Model):
    """
    Used to track how many Components are used per Product.
    """
    name = models.CharField(max_length=100, blank=True, help_text="Optional; enter a memorable name for this ratio.")
    component = models.ForeignKey(Product, limit_choices_to = {'is_component__exact': '1'})
    ratio = models.DecimalField(max_digits=7, decimal_places=4, help_text="Enter the number of components used per product. Express fractions as decimal values; eg. if a job is run 4 up, enter 0.25.")

    def __unicode__(self):
        if self.name:
            return u'%s' % self.name
        return u'%s x %s' % (self.ratio, self.component)
