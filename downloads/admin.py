from django.contrib import admin
from .models import Download

class DownloadAdmin(admin.ModelAdmin):
    pass

admin.site.register(Download, DownloadAdmin)
