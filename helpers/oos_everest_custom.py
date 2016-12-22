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
from . import settings
from products.models import Product, Category, ComponentRatio
from orgs.models import Org, UserProfile
from orders.models import Order, OrderedItem
from helpers.views import price_calc
from helpers.reporter import ReportFormatter
from sys import exit
import csv
import datetime
from StringIO import StringIO

setup_environ(settings)

REPORT_FNAME = '/tmp/everest-stationery.xlsx'
PRODUCTS_OF_INTEREST = [1994, 145, 1585, 147, 148, 149, 150, 151, 152, 153, 753, 2088, 154, 155, 156, 157, 158, 159, 160, 161, 162, 163, 164, 165, 166, 167, 168, 169, 170] # only interested in these products
subject = '[Mimic OOS] Monthly Everest Stationery Report'
formatter = ReportFormatter('Monthly Everest Stationery Report')
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
        items = OrderedItem.objects.filter(~Q(inventory_history__product__part_number__startswith='***'), order=o, inventory_history__product__pk__in=PRODUCTS_OF_INTEREST)
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
body = 'Attached is the custom monthly Everest report for orders placed in month %s of %s.' % (ordered_during_month, ordered_during_year)

email = EmailMessage(
    subject,
    body,
    'admin@mimicprint.com',
    ['romana.mirza@mimicprint.com', 'laura.ambrozic@mimicprint.com', 'daniel@threedata.com',],
)
email.attach_file(REPORT_FNAME)
email.send()
