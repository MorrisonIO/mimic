from django import forms
from django.contrib import admin, messages
from django.db.models import Q, CharField
from django.core import urlresolvers
from django.shortcuts import redirect
from daterange_filter.filter import DateRangeFilter
from .views import subtract_inventory

from .models import Order, InventoryHistory, OrderedItem, WorkNote
from products.models import Product
from uploads.models import Upload
from orgs.models import Org
from products.models import Product

class FastOrderForm(forms.ModelForm):
    org_choices = [('', '---------'),]
    product_choices = [('', '---------'),]
    try:
        org_choices += [(org.id, org.name) for org in Org.objects.all()]
        product_choices += [(prod.id, prod.name) for prod in Product.objects.all()]
    except Exception as ex:
        print "Error FastOrderForm: {}".format(ex)
    job_product = forms.ChoiceField(required=True, choices=product_choices, widget=forms.Select(attrs={'class':'required'}))
    job_qty = forms.IntegerField(required=True, widget=forms.TextInput(attrs={'size':'5', 'class':'required'}))

class OrderAdmin(admin.ModelAdmin):
    list_filter = ('status', ('due_date', DateRangeFilter), ('date', DateRangeFilter), 'org')
    list_display = ('name', 'org', 'date', 'due_date', 'status', 'descriptions', 'part_numbers', 'quantity', 'notes', 'po',
                    'docket_link', 'printed_button', 'shipping_links', 'invnum_form')
    search_fields = ('name', 'invoice_number', 'status', 'org__name', 'po_number')
    raw_id_fields = ('ship_to',)
    date_hierarchy = ('date')
    form = FastOrderForm


    def get_fieldsets(self, request, obj=None):
        fieldsets = super(OrderAdmin, self).get_fieldsets(request, obj)
        self.exclude += ('job_product', 'job_qty',)
        return fieldsets

    def get_form(self, request, obj=None, **kwargs):
        additional_file = obj.additional_file if obj else None
        username = request.user.username
        self.exclude = ()

        self.raw_id_fields = ()
        if not (request.user.is_superuser or request.user.is_staff):
            self.exclude = ('shipping_date',)
        self.exclude += ('saved',)

        form = super(OrderAdmin, self).get_form(request, obj, **kwargs)
        if not additional_file:
            form.base_fields['additional_file'].queryset = form.base_fields['additional_file'] \
                                                                        .queryset \
                                                                        .filter(user_name=username)
        else:
            id_filter = Q(pk=additional_file.id)
            name_filter = Q(user_name=username) 
            form.base_fields['additional_file'].queryset = form.base_fields['additional_file'] \
                                                                    .queryset \
                                                                    .filter(id_filter | name_filter)

        return form

    def po(self, obj):
        """
        Display po_number like 'PO'
        """
        return obj.po_number

    def notes(self, obj):
        """
        Display worknotes like 'NOTES'
        """
        link = '/admin/orders/worknote/add/'
        return u'<a href="%s">%s</a>' % (link,'Add note')

    notes.allow_tags=True

    def descriptions(self, obj):
        """
        Display all products descriptions included in this order
        """
        products_descriptions = ''
        ih_objs = InventoryHistory.objects.filter(order_id=obj.id)
        if len(ih_objs):
            products_descriptions = ',\n'.join(Product.objects.get(id=el.product_id).description for el in ih_objs \
                                            if Product.objects.get(id=el.product_id).description)
        return products_descriptions

    def part_numbers(self, obj):
        """
        Display all products part numbers included in this order
        """
        products_pns = ''
        ih_objs = InventoryHistory.objects.filter(order_id=obj.id)
        if len(ih_objs):
            products_pns = ',\n'.join(Product.objects.get(id=el.product_id).part_number for el in ih_objs \
                                            if Product.objects.get(id=el.product_id).part_number)
        return products_pns

    def quantity(self, obj):
        """
        Display total products amount in this order
        """
        total = 0
        ih_objs = InventoryHistory.objects.filter(order_id=obj.id)
        products_descriptions = sum(el.amount for el in ih_objs if el.amount)
        return products_descriptions

    def save_model(self, request, obj, form, change):
        """
        Saving order object and creation InventoryHistory and OrderItem records in DB
        """
        super(OrderAdmin, self).save_model(request, obj, form, change)

        obj.user = request.user
        amount  = request.POST.get('job_qty', [])

        if not change and amount:
            try:
                product_id = request.POST.get('job_product', [])
                product = Product.objects.get(pk=product_id)
                subtract_inventory(product, obj, amount, obj.placed_by, 'Admin order', obj.date)
            except Exception as ex:
                messages.warning(request, 'Order has no been saved. \
                                        Please check data on fields and try again.')
                redirect('/admin/orders/order')
        else:
            messages.warning(request, 'Order has no been saved. \
                                        Please check data on fields and try again.')
            redirect('/admin/orders/order')


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

    class Media:
        js = ('admin/js/worknote.js',)


admin.site.register(Order, OrderAdmin)
admin.site.register(InventoryHistory, InventoryHistoryAdmin)
admin.site.register(OrderedItem, OrderedItemAdmin)
admin.site.register(WorkNote, WorkNoteAdmin)
