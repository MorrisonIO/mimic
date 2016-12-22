from django.db import models
from django.db.models import permalink
from django.contrib.auth.models import User
from orgs.models import Org, UserProfile
from products.models import Product, Category
from orders.models import Order
from django.core import serializers
from django.db.models.query import QuerySet
import datetime

### TODO: requires refactoring

def get_last_day_of_month(year, month):
    """
    Returns a datetime object of the last day of the month specified by 'year' and 'month'.
    """
    if (month == 12):
        year += 1
        month = 1
    else:
        month += 1
    return datetime.date(year, month, 1) - datetime.timedelta(1)

def get_prev_month(year, month):
    """
    Returns a datetime object of the first day of the month previous to the one specified by 'year' and 'month'.
    """
    if (month == 1):
        year -= 1
        month = 12
    else:
        month -= 1
    return datetime.datetime(year, month, 1, 0, 0, 0, 0)

def get_quarter_starts(first_quarter_start):
    """
    Returns a dictionary of four datetime objects representing months that fiscal quarters start. The day of the datetimes returned is be the first of each month in question. 'first_quarter_start' is an integer between 1 and 12.
    """
    today = datetime.date.today()
    year = today.year
    if first_quarter_start > today.month:
        year -= 1
    second_year = year
    third_year = year
    fourth_year = year

    first_month = first_quarter_start

    second_month = first_month + 3
    if second_month > 12:
        second_month -= 12
        second_year += 1

    third_month = first_month + 6
    if third_month > 12:
        third_month -= 12
        third_year += 1

    fourth_month = first_month + 9
    if fourth_month > 12:
        fourth_month -= 12
        fourth_year += 1

    first_quarter = datetime.datetime(year, first_month, 1, 0,0,0,0)
    second_quarter = datetime.datetime(second_year, second_month, 1, 0,0,0,0)
    third_quarter = datetime.datetime(third_year, third_month, 1, 0,0,0,0)
    fourth_quarter = datetime.datetime(fourth_year, fourth_month, 1, 0,0,0,0)
    quarters = [first_quarter, second_quarter, third_quarter, fourth_quarter]

    return quarters

def get_which_quarter(quarter_starts):
    """
    Returns which quarter we are currently in, based on quarterly start dates as determined by the quarter_starts method.
    """
    now = datetime.datetime.now()
    first_quarter = quarter_starts[0]
    second_quarter = quarter_starts[1]
    third_quarter = quarter_starts[2]
    fourth_quarter = quarter_starts[3]
    if first_quarter < now < second_quarter:
        return 1
    if second_quarter < now < third_quarter:
        return 2
    if third_quarter < now < fourth_quarter:
        return 3
    return 4

class SerializedArrayField(models.CharField):
    def __init__(self, *args, **kwargs):
        super(SerializedArrayField, self).__init__(*args, **kwargs)

    def _serialize(self, value):
        if not value:
            return ''

        return ','.join(value)

    def _deserialize(self, value):
        return value.split(',')

    def db_type(self):
        return 'text'

    def pre_save(self, model_instance, add):
        value = getattr(model_instance, self.attname, None)
        return self._serialize(value)

    def contribute_to_class(self, cls, name):
        self.class_name = cls
        super(SerializedArrayField, self).contribute_to_class(cls, name)
        models.signals.post_init.connect(self.post_init)

    def post_init(self, **kwargs):
        if 'sender' in kwargs and 'instance' in kwargs:
            if kwargs['sender'] == self.class_name and \
            hasattr(kwargs['instance'], self.attname):
                value = self.value_from_object(kwargs['instance'])

                if value:
                    setattr(kwargs['instance'], self.attname,
                            self._deserialize(value))
                else:
                    setattr(kwargs['instance'], self.attname, None)


class Report(models.Model):
    """
    A report is a set of constraints used to build a database query so that the user may view a subset of existing orders.
    """

    DEFAULT_STATES = [x[0] for x in Order.STATUS_CHOICES]

    name = models.CharField(max_length=200, blank=True)
    owner = models.ForeignKey(User, related_name="reports_owner_set")
    is_visible = models.BooleanField()
    daterange_type = models.CharField(max_length=2, blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    quarter_start = models.CharField(max_length=2, blank=True, null=True)
    last_orders = models.PositiveIntegerField(max_length=3, blank=True, null=True)
    orgs = models.ManyToManyField(Org, blank=True)
    products = models.ManyToManyField(Product, blank=True)
    ordered_by = models.ManyToManyField(UserProfile, blank=True, null=True, related_name="reports_ordered_by_set")
    categories = models.ManyToManyField(Category, blank=True, null=True)
    states = SerializedArrayField(default=",".join(DEFAULT_STATES), max_length=255)
    scheduled = models.BooleanField()
    schedule = models.CharField(max_length=100, default='* * * * *')

    def __unicode__(self):
        return u'%s' % self.name

    @permalink
    def get_absolute_url(self):
        return ('report_detail', None, { 'report_id': self.id })

    def _calc_dates(self):
        now = datetime.datetime.now()

        if self.daterange_type == 'tm': # this month
            start_date = datetime.datetime(now.year, now.month, 1, 0, 0, 0, 0)
            end_date = now

        elif self.daterange_type == 'lm': # last month
            start_date = get_prev_month(now.year, now.month)
            end_date = datetime.datetime(now.year, now.month, 1, 23, 59, 59, 0) - datetime.timedelta(days=1)

        elif (self.daterange_type == 'tq') or (self.daterange_type == 'lq'):
            quarters = get_quarter_starts(int(self.quarter_start)) # find out when quarters start
            quarter = get_which_quarter(quarters) # which quarter we're currently in
            if self.daterange_type == 'lq':
                quarter -= 1 # show last quarter instead
            if quarter == 0: # we're in q1 and showing last quarter
                q = quarters[3]
                start_date = datetime.datetime(q.year - 1, q.month, 1, 0,0,0,0)
                end_date = quarters[0]
            if quarter == 1:
                start_date = quarters[0]
                end_date = quarters[1]
            if quarter == 2:
                start_date = quarters[1]
                end_date = quarters[2]
            if quarter == 3:
                start_date = quarters[2]
                end_date = quarters[3]
            if quarter == 4: # only reach this if we are showing this quarter
                q = quarters[0]
                start_date = quarters[3]
                end_date = datetime.datetime(q.year + 1, q.month, 1, 23,59,59,0)

        elif self.daterange_type == 'fd':
            s = self.start_date # date object
            e = self.end_date
            start_date = datetime.datetime(s.year, s.month, s.day, 0,0,0,0)
            end_date = datetime.datetime(e.year, e.month, e.day, 23,59,59,0)

        else: # all orders, or fixed number
            start_date = datetime.datetime(1900, 1, 1, 0, 0, 0, 0) # shouldn't be any orders earlier than 1900 (I hope!)
            end_date = now

        self._current_start_date = start_date
        self._current_end_date = end_date

    @property
    def current_start_date(self):
        if not hasattr(self, '_current_start_date'):
            self._calc_dates()

        return self._current_start_date

    @property
    def current_end_date(self):
        if not hasattr(self, '_current_end_date'):
            self._calc_dates()

        return self._current_end_date

    def orders(self, download = False, user = None):
        # Filter by org:
        orgs = self.orgs.all()
        if not orgs:
            orgs = Org.objects.filter(userprofile__user=(user or self.owner))

        self.reported_orgs = orgs

        categories = self.categories.all()
        if not categories:
            categories = Category.objects.filter(org__in=orgs)

        self.reported_categories = categories

        # Filter by products:
        if self.products.count() > 0:
            prods = self.products.filter(categories__in=categories)
        else:
            prods = Product.objects.filter(categories__in=categories, status__exact='av')

        self.reported_prods = prods

        # Filter by user:
        userprofiles = self.ordered_by.all()
        if not userprofiles:
            userprofiles = UserProfile.objects.filter(org__in=orgs)

        self.reported_userprofiles = userprofiles

        if download:
            sorter = ['org', 'due_date']
        else:
            sorter = ['due_date']

        # Now get the orders from the db
        result = Order.objects.filter(
                    due_date__range=(self.current_start_date, self.current_end_date),
                    org__in=orgs,
                    placed_by__userprofile__in=userprofiles,
                    ordereditem__inventory_history__product__in=prods,
                    status__in=self.states
                ).order_by(*sorter).distinct()

        # Filter by fixed number:
        if self.last_orders:
            result = result[:self.last_orders]

        return result
