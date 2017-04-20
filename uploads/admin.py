from django.contrib import admin

from .models import Upload

class UploadAdmin(admin.ModelAdmin):
    list_filter = ('name', 'date_added', 'user_name')
    list_display = ('name', 'date_added', 'user_name')

admin.site.register(Upload, UploadAdmin)
