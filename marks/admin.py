from django.contrib import admin
from .models import Marks


@admin.register(Marks)
class MarksAdmin(admin.ModelAdmin):
    list_display = (
        'get_student_id', 'subject', 'get_institution',
        'total_marks', 'grade', 'grade_point', 'status', 'entered_by', 'created_at'
    )
    list_filter = ('institution', 'status', 'subject__program')
    search_fields = (
        'exam_registration__student__student_id',
        'exam_registration__student__user__first_name',
        'subject__name', 'subject__code'
    )
    raw_id_fields = ('exam_registration', 'subject', 'entered_by')
    ordering = ('-created_at',)

    @admin.display(description='Student ID')
    def get_student_id(self, obj):
        return obj.exam_registration.student.student_id

    @admin.display(description='Institution')
    def get_institution(self, obj):
        return obj.institution
