from django.contrib import admin
from models import Report
from orders.models import Order
from django import forms

class ReportAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(ReportAdminForm, self).__init__(*args, **kwargs)
        self.fields['states'].widget = forms.SelectMultiple(choices=Order.STATUS_CHOICES)

    def clean_states(self):
        data = [x for x in self.data.getlist('states') if x in Report.DEFAULT_STATES]
        if not data:
            raise forms.ValidationError('States required')
        return data

class ReportAdmin(admin.ModelAdmin):
    form = ReportAdminForm

    class Media:
        css = {
            'all': ('css/jquery-cron.css', 'css/jquery-gs.css')
        }

        js = ('js/jquery-1.3.2.min.js', 'js/jquery-gs.js', 'js/jquery-cron.js', 'js/init-cron.js')


admin.site.register(Report, ReportAdmin)
