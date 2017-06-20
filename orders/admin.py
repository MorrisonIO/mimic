from django.contrib import admin
from django.db.models import Q, CharField
from .models import Order, InventoryHistory, OrderedItem, WorkNote
from daterange_filter.filter import DateRangeFilter
from products.models import Product

from uploads.models import Upload

class OrderAdmin(admin.ModelAdmin):
    list_filter = ('status', ('due_date', DateRangeFilter), ('date', DateRangeFilter), 'org')
    list_display = ('name', 'org', 'date', 'due_date', 'status', 'descriptions', 'part_numbers', 'quantity_required', 'worknotes_links', 'po_number',
                    'docket_link', 'printed_button', 'shipping_links', 'invnum_form')
    search_fields = ('name', 'invoice_number', 'status', 'org__name', 'po_number')
    raw_id_fields = ('ship_to',)
    date_hierarchy = ('date')

    def get_form(self, request, obj=None, **kwargs):
        additional_file = obj.additional_file if obj else None
        username = request.user.username
        self.exclude = ()
        if not (request.user.is_superuser or request.user.is_staff):
            self.exclude = ('shipping_date',)
        self.exclude += ('saved',)
        form = super(OrderAdmin, self).get_form(request, obj, **kwargs)
        if not additional_file:
            form.base_fields['additional_file'].queryset = form.base_fields['additional_file'] \
                                                                        .queryset \
                                                                        .filter(user_name=username)
        else:
            form.base_fields['additional_file'].queryset = form.base_fields['additional_file'] \
                                                                        .queryset \
                                                                        .filter( Q(pk=additional_file.id) | Q(user_name=username) )

        return form


    def descriptions(self, obj):
        products_descriptions = ''
        ih_objs = InventoryHistory.objects.filter(order_id=obj.id)
        if len(ih_objs):
            products_descriptions = '\n'.join(Product.objects.get(id=el.product_id).description for el in ih_objs \
                                            if Product.objects.get(id=el.product_id).description)
        return products_descriptions


    def part_numbers(self, obj):
        products_pns = ''
        ih_objs = InventoryHistory.objects.filter(order_id=obj.id)
        if len(ih_objs):
            products_pns = '\n'.join(Product.objects.get(id=el.product_id).part_number for el in ih_objs \
                                            if Product.objects.get(id=el.product_id).part_number)
        return products_pns


    def quantity_required(self, obj):
        total = 0
        ih_objs = InventoryHistory.objects.filter(order_id=obj.id)
        products_descriptions = sum(el.amount for el in ih_objs if el.amount)
        return products_descriptions


class InventoryHistoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'link_to_order', 'date', 'notes')
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
    raw_id_fields = ('order',)

admin.site.register(Order, OrderAdmin)
admin.site.register(InventoryHistory, InventoryHistoryAdmin)
admin.site.register(OrderedItem, OrderedItemAdmin)
admin.site.register(WorkNote, WorkNoteAdmin)
