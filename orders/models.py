from django.db import models
from django.db.models import permalink
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.template import RequestContext, loader, Context
from django.core.mail import send_mail, mail_managers
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.conf import settings
from products.models import Product
from orgs.models import Org
from addresses.models import Address
import string
import array
from time import time
import random

class Item:
    """
    One Product in a Cart -- one thing that the user intends to order.

    A unique_id is also stored along with the product for each item in a cart,
    since in the case of variable items there might be more than one instance
    of the same product being ordered, and when modifying
    or deleting there needs to be a way to distinguish between them.
    """
    def __init__(self, product, unique_id, quantity):
        self.product = product
        self.unique_id = unique_id
        self.quantity = quantity


class Cart:
    """
    An ongoing order. Carts have one or more Items in them.
    """
    def __init__(self):
        self.items = []

    def has_items(self):
        """
        Returns true if a Cart has Items in it.
        """
        return len(self.items) != 0

    def has_item(self, product):
        """
        Returns an Item if the specified product is already in the cart.
        """
        for item in self.items:
            if item.product == product:
                return item

    def has_item_by_unique_id(self, unique_id):
        """
        Returns an Item if an Item with the unique_id is already in the cart.
        """
        for item in self.items:
            if item.unique_id == unique_id:
                return item

    def all_items(self):
        return self.items

    def add_item(self, product, unique_id, quantity):
        """
        Adds an Item to a Cart. This method is also used
        when modifying an Item already in a Cart;
        in that case, the existing quantity is overwritten
        (instead of adding another of the same product).
        """
        item_in_cart = self.has_item_by_unique_id(unique_id)
        if item_in_cart:
            item_in_cart.quantity = quantity
        else:
            item = Item(product, unique_id, quantity)
            self.items.append(item)

    def incr_item(self, product, quantity):
        """
        Increments the amount ordered for an Item already in the cart.
        """
        item = self.has_item(product)
        if item:
            new_qty = quantity + item.quantity
            item.quantity = new_qty

    def delete_item(self, unique_id):
        """
        Deletes an Item out of a Cart.
        """
        item = self.has_item_by_unique_id(unique_id)
        if item:
            self.items.remove(item)


class Order(models.Model):
    """
    An Order is created when the user completes the 'checkout' procedure:
     adding products to a Cart, choosing a shipto recipient, etc and submitting the form.
    """
    STATUS_CHOICES = (
        ('pa', 'Pending Approval'), # A product on the order is flagged as requiring manager approval
        ('po', 'Awaiting PO'),      # Like pending approval (order is on hold) but client must provide PO
        ('ac', 'Active'),           # The order is in production
        ('co', 'Completed'),        # The product(s) have been produced in production
        ('ps', 'Partial Shipped'),  # The order has been partly shipped
        ('sh', 'Shipped'),          # The order has left the building
        ('in', 'Invoiced'),         # The order has been invoiced
        ('ca', 'Cancelled'),        # The order has been cancelled
    )
    name = models.CharField(max_length=200)
    placed_by = models.ForeignKey(User, related_name="orders_placed_by_set")
    org = models.ForeignKey(Org)
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)
    date = models.DateTimeField('Placed on', blank=True)
    due_date = models.DateField(help_text="yyyy-mm-dd")
    po_number = models.CharField("P.O. number", max_length=50, blank=True)
    approved_by = models.ForeignKey(User, blank=True, null=True, related_name="orders_approved_by_set")
    approved_date = models.DateTimeField('Approved on', blank=True, null=True)
    ship_to = models.ForeignKey(Address)
    additional_info = models.TextField(blank=True, help_text="Any additional details Mimic might require to complete this order.", null=True)
    invoice_number = models.CharField(max_length=200, blank=True, null=True)
    user_notes = models.TextField("Your notes", blank=True, help_text="Any information you wish to save with this order for your own records.", null=True)
    saved = models.BooleanField(blank=True, default=False) # field might be DEPRECATED

    def __unicode__(self):
        return u'%s' % self.name

    @permalink 
    def get_absolute_url(self):
        return ('orders:order_detail', None, { 'order_id': self.id })

    class Meta:
        ordering = ['-date']

    def make_name(self):
        """
        Creates a unique name for an order, like "WGDF-1176315805".
        """
        txt = ''
        num = str(time()).split('.')[0] # num of seconds since epoch
        # 4 random consonants. No vowels so we don't get any, uh, 4 letter words. :-p
        chars = random.sample(['B','C','D','F','G','H','J','K','L','M','N','P','Q','R','S','T','V','W','X','Z'], 4) 
        for c in chars: txt += c
        return u'%s-%s' % (txt, num)

    def get_line_items(self):
        """
        Returns a list of dictionaries corresponding to each ordered item on this Order.
        """
        ordered_items = OrderedItem.objects.filter(order=self)
        line_items = []
        for item in ordered_items:
            inventory_history = InventoryHistory.objects.get(pk=item.inventory_history.id)
            line_items.append(inventory_history.get_line_item())
        return line_items

    def get_status_explanation(self):
        """
        Returns a plain English sentence explaining the various order statuses.
        """
        if self.status == 'pa':
            return "There is a product on the order that has been flagged as \
            requiring approval from a manager before it can be placed into production. \
            Please note that we take no action on all items on this order \
            until approval has been received. When this order is approved, its status will change to Active."
        elif self.status == 'ac':
            return "It is currently in production at Mimic Print & Media Services."
        elif self.status == 'co':
            return "Production has finished and it is ready to be shipped."
        elif self.status == 'sh':
            return "It is en route to the ship-to address selected, or has been made available for pickup, whichever is appropriate."
        elif self.status == 'in':
            return "Invoice number %s has been prepared and sent." % self.invoice_number
        return ''

    def worknotes_links(self):
        """
        Adds the link to view/edit the workflow notes for this order.
        """
        try:
            worknote = WorkNote.objects.get(order=self)
            return '<a href="/admin/orders/worknote_view/%s/" title="%s">View</a>\
             / <a href="/admin/orders/worknote/%s/">Edit</a>' % (worknote.id, worknote.status, worknote.id)
        except: 
            return '<a href="/admin/orders/worknote/add/">Add</a>'
    worknotes_links.allow_tags = True  # allow HTML tags
    worknotes_links.short_description = 'Work notes'

    def docket_link(self):
        """
        Add a create docket link to the Orders change list in the admin.
        """
        return '<a href="/admin/orders/dockets/%s/">Create</a>' % self.id
    docket_link.allow_tags = True  # allow HTML tags
    docket_link.short_description = 'Docket'

    def shipping_links(self):
        """
        Add the shipping links to the Orders change list in the admin.
        """
        return '<a href="/admin/orders/shipping/packing_slip/%s/">PS</a>\
         | <a href="/admin/orders/shipping/label/%s/">L</a> | <a href="/admin/orders/shipping/comm_inv/%s/">CI</a>' % (self.id, self.id, self.id)
    shipping_links.allow_tags = True  # allow HTML tags
    shipping_links.short_description = 'Shipping'

    def invnum_form(self):
        """
        Add a form for adding invoice numbers to the Orders change list in the admin.
        """
        if self.invoice_number:
            return self.invoice_number
        else:
            return '<form action="/admin/orders/save_invnum/" method="post">\
            <input type="text" size="10" name="invoice_number">\
            <input type="hidden" name="order_id" value="%s">\
            <input type="submit" value="&gt;"></form>' % self.id
    invnum_form.allow_tags = True  # allow HTML tags
    invnum_form.short_description = 'Invoice Number'


class InventoryHistory(models.Model):
    """
    An inventory history is an event where a product's inventory changes:
    typically this is either an order, or a manual adjustment
    (eg after a recount, or when new products are created).

    Note that because OrderedItems reference this model,
    an InventoryHistory event is generated whenever an order is placed
     *regardless* of whether we are tracking inventory on the product in question.
    """
    product = models.ForeignKey(Product)
    order = models.ForeignKey(Order, blank=True, null=True, help_text="<strong>Leave this blank</strong>\
     if you are making a manual adjustment to inventory levels.")
    amount = models.IntegerField(max_length=15, help_text="Enter the amount the inventory is changing by,\
         <em>not</em> the new inventory level. \
         You may enter negative numbers. \
         For example, if you are adding 100 pieces of stock,\
         enter 100; if physical inventory is 25 less\
         than what it should be, enter -25.")
    modified_by = models.ForeignKey(User)
    notes = models.CharField(max_length=200, help_text="Enter a short note describing what this change is.")
    date = models.DateTimeField()

    def __unicode__(self):
        return "%s (%s)" % (self.product, self.date)

    class Meta:
        verbose_name_plural = "Inventory events"

    def save(self):
        """
        Define a custom save function since the inventory level
        that's set in the Product also potentially needs to be modified.
        Note that if this change is coming from an online order,
        the amount (which will be positive) needs to be *subtracted* from inventory,
        but if it's coming via a manual change in the admin, a positive amount needs to be *added*
        (and a negative amount can be added as well, effectively subtracting it).
        """
        super(InventoryHistory, self).save()
        if self.product.track_inventory:
            if not self.product.inventory:  # adding for the first time
                self.product.inventory = 0
            if self.order:
                self.product.inventory -= self.amount
            else:
                self.product.inventory += self.amount
            self.product.save()
            if self.product.inventory < self.product.replenish_threshold:
                site = Site.objects.get_current()
                t = loader.get_template('emails/inventory_replenish_alert.txt')
                subject = "[Mimic OOS] Inventory Alert: %s" % self.product
                c = Context({
                    'order': self.order,
                    'product': self.product,
                    'replenish_threshold': self.product.replenish_threshold,
                    'inventory': self.product.inventory,
                    'site': site,
                })
                body = t.render(c)
                # not possible to mail Mimic account reps, as that requires knowing
                # the current Org (part of the request object which we have no access to)
                mimic_list = ["Replenishment <replenishment@mimicprint.com>"]
                send_mail(subject, body, 'orders@mimicprint.com', mimic_list, fail_silently=False)
        return

    def get_line_item(self):
        """
        Returns a dictionary of quantity, product name, any variable data, and additional details (part number, revision, link) of an ordered product. Called by get_text_line_item() and get_html_line_item() below.
        """
        var_data = {}
        href_path = ''
        oi = OrderedItem.objects.get(inventory_history=self)
        if self.product.is_variable:
            from vardata.models import *
            model = self.product.var_form.replace('Form', '')
            var_form = eval(model)
            var_data = var_form.objects.get(ordereditem=oi)
            href_path = '%s/%s/%s/' % ('/oos/vardata', self.product.var_form, oi.id)
        return {
            'quantity': self.amount,
            'name': self.product.name,
            'part_number': self.product.part_number or '',
            'revision': self.product.revision or '',
            'href_path': href_path,
            'var_data': var_data,
        }


class OrderedItem(models.Model):
    """
    An ordered item is one product on an order.
    An order is made up of one or more ordered items.
    """
    order = models.ForeignKey(Order)
    inventory_history = models.ForeignKey(InventoryHistory)

    def __unicode__(self):
        return u'%s' % self.inventory_history.product.name

class WorkNote(models.Model):
    """
    Used to keep track of current progress of work on an order -- who's done what,
    current status, etc -- basically a freeform area to jot notes in.
    """
    order = models.ForeignKey(Order, unique=True)
    staff = models.ManyToManyField(User,
                                   help_text="Select the Mimic employees involved in this order.",
                                   verbose_name="Mimic staff",
                                   limit_choices_to={'is_staff__exact': '1'})
    status = models.CharField(max_length=200, help_text="Enter a short summary of the progress of this order.")
    notes = models.TextField(help_text="<p class='help'>Enter any workflow related notes here. Formatting hints:</p>\
                                        <p class='help'>Make text <tt>*italic* or __bold__</tt>; full links become clickable\
                                        <br>End a line with 2 or more spaces for a carriage return, double-space for paragraphs\
                                        <br>Make a line with <tt>---</tt>, a header with <tt>### Something</tt><br>\
                                        Make a bullet list with <tt>* item</tt> on separate lines, a numbered list with <tt>1. \
                                        item</tt><br>To colour-code your text, surround it with your uppercase initials like this: \
                                        <tt>DC David wrote this /DC</tt></p>", blank=True)
    mail_staff = models.BooleanField(blank=True, help_text="If selected, the staff selected above will be notified by mail when this note is saved.")
    last_modified = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'Work notes for %s' % self.order

    def save(self):
        """
        Custom save method to enable sending email out if necessary.
        """
        super(WorkNote, self).save()
        if self.mail_staff:
            site = Site.objects.get_current()
            t = loader.get_template('emails/worknote_updated.txt')
            c = Context({
                'worknote': self,
                'site': site,
            })
            subject = "[Mimic OOS] WorkNote Updated: %s" % self.order
            body = t.render(c)
            staff_list = []
            for s in self.staff.all():
                addr = "%s %s <%s>" % (s.first_name, s.last_name, s.email)
                staff_list.append(addr)
            send_mail(subject, body, 'orders@mimicprint.com', staff_list, fail_silently=False)
