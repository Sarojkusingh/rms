from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'institution', 'is_active', 'is_staff')
    list_filter = ('role', 'is_active', 'is_staff', 'institution')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('-date_joined',)
    fieldsets = BaseUserAdmin.fieldsets + (
        ('RMS Info', {
            'fields': ('role', 'institution', 'phone', 'profile_picture')
        }),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('RMS Info', {
            'fields': ('role', 'institution', 'phone')
        }),
    )
