import os

from django.db.models import FileField
from django.contrib import admin
from models import Product, Category, ComponentRatio

class CategoryAdmin(admin.ModelAdmin):
    list_filter = ('org',)
    fieldsets = (
        ('Details', {
            'fields': ('name', 'org')
        }),
        ('Options', {
            'classes': ('collapse',),
            'fields': ('name_altname', ('revision_altname', 'show_revision'), ('part_number_altname', 'show_part_number'), ('price_altname', 'show_price'), 'show_inventory', 'sort')
        }),
    )

class ProductAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Details', {
            'fields': (('name', 'is_component'), 'description', 'categories', 'status', 'preview', 'revision', 'part_number', 'price', 'sort')
        }),
        ('Ordering rules', {
            'classes': ('collapse',),
            'fields': ('min_order_qty', 'fixed_order_qtys', 'approval_required', ('is_variable', 'var_form'))
        }),
        ('Inventory', {
            'classes': ('collapse',),
            'fields': ('track_inventory', 'inventory', 'replenish_threshold', 'warehouse_location')
        }),
        ('Internal Instructions', {
            'classes': ('collapse',),
            'fields': ('ratios', 'page_count', 'prepress_info', 'bw_info', 'colour_info', 'bindery_info', 'shipping_info', 'billing_info', 'outsourcing_info', ('is_fsc', 'paper_type', 'logo_position', 'smartwood_proof'))
        }),
    )
    list_display = ('name', 'part_number', 'revision', 'in_categories')
    list_filter = ('status', 'is_component', 'is_variable')
    search_fields = ('name', 'description', 'part_number')

    def save_form(self, request, form, change):
        """Deletes the file from fields FileField/ImageField if
        their values have changed"""

        obj = form.instance
        if obj:
            for field in obj._meta.fields:
                if not isinstance(field, FileField):
                    continue

                path = getattr(obj, field.name, None)
                if path:
                    if field.name in form.changed_data or form.data.get('clear_image_'+field.name, ''):
                        try:
                            os.unlink(path.path)
                        except OSError:
                            pass
                        setattr(obj, field.name, None)

        return super(ProductAdmin, self).save_form(request, form, change)

class ComponentRatioAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Details', {
            'fields': ('component', 'ratio', 'name')
        }),
    )

admin.site.register(Category, CategoryAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(ComponentRatio, ComponentRatioAdmin)
