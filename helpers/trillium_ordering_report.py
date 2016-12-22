#!/usr/bin/env python
#
# trillium_ordering_report.py
# Generates a custom report of the ordering history of Trillium College
# output as a csv file and emailed.
#

from django.core.mail import EmailMessage
from django.core.management import setup_environ
from django.contrib.auth.models import User
from . import settings
from products.models import Product, Category, ComponentRatio
from orgs.models import Org, UserProfile
from orders.models import Order, OrderedItem
import csv
import datetime
import StringIO
from tempfile import NamedTemporaryFile

setup_environ(settings)


class UnicodeWriter(object):
    """
    Like UnicodeDictWriter, but takes lists rather than dictionaries.
    
    Usage example:
    
    fp = open('my-file.csv', 'wb')
    writer = UnicodeWriter(fp)
    writer.writerows([
        [u'Bob', 22, 7],
        [u'Sue', 28, 6],
        [u'Ben', 31, 8],
        # \xc3\x80 is LATIN CAPITAL LETTER A WITH MACRON
        ['\xc4\x80dam'.decode('utf8'), 11, 4],
    ])
    fp.close()
    """
    def __init__(self, f, dialect=csv.excel_tab, encoding="utf-16", **kwds):
        # Redirect output to a queue
        self.queue = StringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoding = encoding
    
    def writerow(self, row):
        # Modified from original: now using unicode(s) to deal with e.g. ints
        self.writer.writerow([unicode(s).encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = data.encode(self.encoding)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)
    
    def writerows(self, rows):
        for row in rows:
            self.writerow(row)


##############
# Begin script to output order results
#

title = ['Ordered from Mimic Print & Media Services']
rows = []
rows.append(title)
rows.append('')

friday = datetime.datetime.today() # cronjob set to run on Fridays
monday = friday - datetime.timedelta(days=5)

campuses = Org.objects.filter(name__startswith="Trillium")

for campus in campuses:
    campus_header = ['%s' % campus]
    rows.append(campus_header)
    orders = Order.objects.filter(org=campus, date__range=(monday, friday)).order_by('date')
    for order in orders:
        item_rows = []
        order_row = ['Order', order]
        date_row = ['Date', '%s-%s-%s' % (order.date.year, order.date.month, order.date.day)]
        item_header = ['Item', 'Part number', 'Description', 'Qty', 'Impr', 'Unit Price', 'Total']
        items = OrderedItem.objects.filter(order=order)
        total = 0
        for item in items:
            product = item.inventory_history.product
            if product.price:
                item_total = product.price * item.inventory_history.amount
            else:
                item_total = 0
            item_row = [item, product.part_number, product.description, item.inventory_history.amount, product.page_count, product.price, item_total]
            item_rows.append(item_row)
            total += item_total
        total_row = ['', '', '', '', '', '', total]

        if len(item_rows): 
            rows.append(order_row)
            rows.append(date_row)
            rows.append('')
            rows.append(item_header)
            for row in item_rows:
                rows.append(row)
            rows.append(total_row)
            rows.append('')
    rows.append('')

fp = NamedTemporaryFile(suffix=".csv")
writer = UnicodeWriter(fp)
writer.writerows(rows)
fp.seek(0)
output = fp.read()


# Send file to Mimic as attachment
body = 'Attached is the Trillium report for orders placed during the week ending %s.' % friday.strftime("%B %d, %Y")
subject = '[Mimic OOS] Weekly Trillium report'
email = EmailMessage(
    subject,
    body,
    'admin@mimicprint.com',
    ['daniel@threedata.com',],
)
email.attach_file(fp.name)
email.send()

fp.close()
