from django.contrib import admin
from authentication.models import User
from django.contrib.auth.admin import UserAdmin

class CustomAdmin(UserAdmin):
    list_display = UserAdmin.list_display + ('role',)
    list_editable = UserAdmin.list_editable + ('role',)

admin.site.register(User,CustomAdmin)
