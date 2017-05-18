from django.contrib import admin
from django.db.models import Q
from models import Order, InventoryHistory, OrderedItem, WorkNote

from uploads.models import Upload

class OrderAdmin(admin.ModelAdmin):
    list_filter = ('status', 'due_date', 'org')
    list_display = ('name', 'org', 'date', 'due_date', 'status', 'worknotes_links', 'po_number',
                    'docket_link', 'printed_button', 'shipping_links', 'invnum_form')
    search_fields = ('name', 'invoice_number')
    raw_id_fields = ('ship_to',)
    date_hierarchy = ('date')
    fieldsets = (
        ('Order info', {'fields': ('name', 'status', 'placed_by',
                                   'org', 'date', 'due_date', 'po_number',
                                   'additional_info', 'approved_by', 'user_notes',
                                   'approved_date', 'printed', 'invoice_number', 'ship_to', 'additional_file')
                       }
        ),
    )

    def get_form(self, request, obj=None, **kwargs):
        form = super(OrderAdmin, self).get_form(request, obj, **kwargs)
        file = obj.additional_file
        username = request.user.username
        print(file)
        if file == None:
            print(type(form.base_fields['additional_file'].queryset.filter(user_name=username)))
            form.base_fields['additional_file'].queryset = form.base_fields['additional_file'].queryset.filter(user_name=username)
        else: 
            form.base_fields['additional_file'].queryset = form.base_fields['additional_file'].queryset.filter(Q(pk=file.id) | Q(user_name=username))
        return form

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
