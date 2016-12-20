#!/usr/bin/env python
#
# oos_everest.py
# Generates a custom report of the ordering history of Everest College
# output as a csv file.
#

from django.core.mail import EmailMessage
from django.core.management import setup_environ
from django.contrib.auth.models import User
from django.db.models import Q
from mimicprint import settings
from mimicprint.products.models import Product, Category, ComponentRatio
from mimicprint.orgs.models import Org, UserProfile
from mimicprint.orders.models import Order, OrderedItem
from mimicprint.helpers.views import price_calc
from mimicprint.helpers.reporter import ReportFormatter
from sys import exit
import csv
import datetime

setup_environ(settings)

REPORT_FNAME = '/tmp/everest-coursewares.xlsx'
CATEGORIES_OF_INTEREST = [24, 25]
subject = '[Mimic OOS] Monthly Everest Coursewares Report'
formatter = ReportFormatter('Monthly Everest Coursewares Report')
formatter.price_calc = price_calc

today = datetime.datetime.today()
yesterday = today - datetime.timedelta(days=1)
ordered_during_month = yesterday.month # cronjob runs on first of month, so we want last month's
ordered_during_year = today.year

campuses = Org.objects.filter(name__startswith="Everest")

item_count = 0
for campus in campuses:
    orders = Order.objects.filter(org=campus, date__month=ordered_during_month, date__year=ordered_during_year).order_by('due_date')
    if not orders:
        continue

    wrote_header = False
    for o in orders:
        items = OrderedItem.objects.filter(~Q(inventory_history__product__part_number__startswith='***'), order=o, inventory_history__product__categories__pk__in=CATEGORIES_OF_INTEREST)
        if items:
            if not wrote_header:
                formatter.section('%s %s' % (campus.client_code, campus))
                wrote_header = True

            formatter.order(o)
            formatter.items(items)
            item_count += len(items)

    if wrote_header:
        formatter.section_end()

if not item_count:
    exit()

formatter.grand_total()
formatter.save(REPORT_FNAME)

# Send file to Mimic as attachment
body = 'Attached is the monthly Everest report for orders placed in month %s of %s.' % (ordered_during_month, ordered_during_year)

email = EmailMessage(
    subject,
    body,
    'admin@mimicprint2.com',
    ['romana.mirza@mimicprint.com', 'laura.ambrozic@mimicprint.com', 'daniel@threedata.com',],
)
email.attach_file(REPORT_FNAME)
email.send()
