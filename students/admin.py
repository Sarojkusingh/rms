from django.contrib import admin
from .models import Student, Enrollment, StudentAcademicHistory


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'get_full_name', 'institution', 'department', 'program', 'semester', 'status', 'created_at')
    list_filter = ('institution', 'status', 'program', 'department', 'semester')
    search_fields = ('student_id', 'registration_number', 'user__first_name', 'user__last_name', 'user__email')
    raw_id_fields = ('user', 'department', 'program', 'semester', 'section', 'academic_session')
    ordering = ('-created_at',)

    @admin.display(description='Full Name')
    def get_full_name(self, obj):
        return obj.user.get_full_name()


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'academic_session', 'semester', 'section', 'enrolled_at')
    list_filter = ('academic_session', 'semester')
    search_fields = ('student__student_id', 'student__user__first_name', 'student__user__last_name')
    raw_id_fields = ('student', 'academic_session', 'semester', 'section')


@admin.register(StudentAcademicHistory)
class StudentAcademicHistoryAdmin(admin.ModelAdmin):
    list_display = ('student', 'cgpa', 'total_credits_completed', 'active_backlogs', 'cleared_backlogs', 'updated_at')
    search_fields = ('student__student_id', 'student__user__first_name')
    raw_id_fields = ('student',)
