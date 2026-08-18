from django.contrib import admin
from .models import Faculty, FacultySubject


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    list_display = ('employee_id', 'get_full_name', 'institution', 'department', 'designation', 'status', 'created_at')
    list_filter = ('institution', 'status', 'department')
    search_fields = ('employee_id', 'user__first_name', 'user__last_name', 'user__email', 'designation')
    raw_id_fields = ('user', 'department')
    ordering = ('-created_at',)

    @admin.display(description='Full Name')
    def get_full_name(self, obj):
        return obj.user.get_full_name()


@admin.register(FacultySubject)
class FacultySubjectAdmin(admin.ModelAdmin):
    list_display = ('faculty', 'subject', 'section', 'academic_session', 'institution', 'allocated_at')
    list_filter = ('institution', 'academic_session')
    search_fields = ('faculty__user__first_name', 'faculty__employee_id', 'subject__name', 'subject__code')
    raw_id_fields = ('faculty', 'subject', 'section', 'academic_session')
