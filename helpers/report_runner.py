from mimicprint import settings
from django.core.management import setup_environ
from django.db import connection
from django.core.mail import EmailMessage
from reports.views import make_report
from reports.models import Report
from django.contrib.auth.models import User, Group
from datetime import datetime
import re
import calendar

class Cron:
    """
    Dead simple cron time specification evaluator against current time.
    TODO: Well, maybe its indeed too many regexps here...
    """

    SPLITTER = re.compile(r'\s+')
    FIELDS = re.compile(r'\s*,\s*')

    EACH_SPEC = r'\*/(\d+)'
    WITHIN_SPEC = '(\d+)-(\d+)'

    EACH = re.compile(r'^\s*' + EACH_SPEC + '\s*$')
    WITHIN = re.compile(r'^\s*' + WITHIN_SPEC + '\s*$')

    ELEMENT_SPEC = r'(?:\*|' + EACH_SPEC + '|' + WITHIN_SPEC + '|-1|\d{1,2})'
    ELIST_SPEC = r'(?:'+ ELEMENT_SPEC + ')(?:,' + ELEMENT_SPEC + ')*'

    TIME_SPEC = re.compile(r'^\s*(' + ELIST_SPEC + '\s+){4}' + ELIST_SPEC + '\s*$')

    class InvalidSpecError(RuntimeError):
        pass

    def __init__(self):
        self.update_time()

    def update_time(self, time = None):
        self.now = time or datetime.today()
        self.dow = self.now.weekday() + 1
        self.last_dom = calendar.monthrange(self.now.year, self.now.month)[1]

        if self.dow == 7:
            self.dow = 0

    def should_run(self, spec):
        if not self.TIME_SPEC.match(spec):
            raise self.InvalidSpecError('Invalid specification')

        spec = self.SPLITTER.split(spec.strip())

        return self._matches(spec[0], self.now.minute) and \
               self._matches(spec[1], self.now.hour)   and \
               self._matches(spec[2], self.now.day)    and \
               self._matches(spec[3], self.now.month)  and \
               self._matches(spec[4], self.dow, {'-1': self.last_dom})

    def _matches(self, spec_str, value, tr={}):
        spec = self.FIELDS.split(spec_str)

        if '*' in spec:
            return True

        for part in spec:
            if part in tr:
                part = tr[part]

            each = self.EACH.match(part)
            within = self.WITHIN.match(part)

            if each:
                if value % int(each.group(1)) == 0:
                    return True
            elif within:
                if int(within.group(1)) <= value <= int(within.group(2)):
                    return True
            elif int(part) == value:
                return True

        return False

def run_report(report_id, target_emails):
    report = Report.objects.get(pk=report_id)

    data = report.orders(True)
    if not data:
        return

    result = make_report(data)

    message = EmailMessage(
            '%s report at %s' % (report.name, datetime.today().strftime('%Y-%m-%d %H:%M:%S')),
            'Attached is the XLSX report %s' % (report.name,),
            'admin@mimicprint.com',
            target_emails
            )

    message.attach('%s.xlsx' % (report.name,), result.save(None), 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    message.send()

def main():
    setup_environ(settings)

    group = Group.objects.get(name='Mimic Staff')

    cursor = connection.cursor()
    cursor.execute('SELECT r.id, r.schedule FROM reports_report r LEFT JOIN auth_user_groups ug ON ug.user_id = r.owner_id WHERE ug.group_id = %s AND r.scheduled = 1', [group.pk])
    
    target_emails = [u.email for u in User.objects.filter(groups=group) if u.email]

    cron = Cron()

    while True:
        row = cursor.fetchone()
        if not row:
            break
        
        if cron.should_run(row[1]):
            run_report(row[0], target_emails)

if __name__ == "__main__":
    main()
