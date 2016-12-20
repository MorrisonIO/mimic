from django.contrib import admin
from models import Org, UserProfile

class OrgAdmin(admin.ModelAdmin):
    pass

class UserProfileAdmin(admin.ModelAdmin):
    list_filter = ['org', ]
    search_fields = ('user__username',)

admin.site.register(Org, OrgAdmin)
admin.site.register(UserProfile, UserProfileAdmin)
