from django.contrib import admin
from .models import Institution, InstitutionSettings


@admin.register(Institution)
class InstitutionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'contact_email', 'contact_phone', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug', 'contact_email')
    prepopulated_fields = {'slug': ('name',)}
    ordering = ('-created_at',)


@admin.register(InstitutionSettings)
class InstitutionSettingsAdmin(admin.ModelAdmin):
    list_display = ('institution', 'result_policy', 'passing_marks', 'is_onboarded', 'onboarding_step')
    list_filter = ('result_policy', 'is_onboarded')
    search_fields = ('institution__name',)
    raw_id_fields = ('institution', 'current_session')
