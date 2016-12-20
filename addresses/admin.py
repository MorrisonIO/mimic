from django.contrib import admin
from .models import Address


class AddressAdmin(admin.ModelAdmin):
    search_fields = ('first_name', 'last_name', 'company', 'address1',)

admin.site.register(Address, AddressAdmin)
