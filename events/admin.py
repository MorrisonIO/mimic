from django.contrib import admin
from models import Entry

class EntryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("title",)}
    list_filter = ('org', 'status')
    list_display = ('title', 'date', 'org', 'status',)
    radio_fields = {"status": admin.HORIZONTAL}
    search_fields = ('docket', 'invoice_number')
    date_hierarchy = ('date')
    

admin.site.register(Entry, EntryAdmin)
