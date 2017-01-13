from django.contrib import admin
from models import Order, InventoryHistory, OrderedItem, WorkNote

class OrderAdmin(admin.ModelAdmin):
    list_filter = ('status', 'due_date', 'org')
    list_display = ('name', 'org', 'date', 'due_date', 'status', 'worknotes_links',
                    'docket_link', 'shipping_links', 'invnum_form')
    search_fields = ('name', 'invoice_number')
    raw_id_fields = ('ship_to',)
    date_hierarchy = ('date')
    fieldsets = (
        ('Order info', {'fields': ('name', 'status', 'placed_by',
                                   'org', 'date', 'due_date', 'po_number',
                                   'additional_info', 'approved_by',
                                   'approved_date', 'invoice_number', 'ship_to')
                       }
        ),
    )

class InventoryHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'order', 'date', 'notes')
    date_hierarchy = ('date')
    search_fields = ('product__name', 'order__name')
    raw_id_fields = ('order', 'product')

class OrderedItemAdmin(admin.ModelAdmin):
    search_fields = ('order__name',)
    raw_id_fields = ('order', 'inventory_history')

class WorkNoteAdmin(admin.ModelAdmin):
    search_fields = ('order__name', 'notes', 'status')
    fieldsets = (
        ('Edit work note', {
            'fields': ('order', 'staff', 'mail_staff', 'status', 'notes')
        }),
    )

admin.site.register(Order, OrderAdmin)
admin.site.register(InventoryHistory, InventoryHistoryAdmin)
admin.site.register(OrderedItem, OrderedItemAdmin)
admin.site.register(WorkNote, WorkNoteAdmin)
