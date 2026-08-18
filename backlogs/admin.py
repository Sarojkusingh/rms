from django.contrib import admin
from .models import Backlog, RevaluationApplication


@admin.register(Backlog)
class BacklogAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'semester', 'institution', 'attempt_number', 'marks_obtained', 'status', 'created_at')
    list_filter = ('institution', 'status', 'semester')
    search_fields = ('student__student_id', 'student__user__first_name', 'subject__name', 'subject__code')
    raw_id_fields = ('student', 'subject', 'semester', 'cleared_in_examination')
    ordering = ('-created_at',)


@admin.register(RevaluationApplication)
class RevaluationApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'get_subject', 'institution', 'old_marks', 'new_marks', 'status', 'fee_paid', 'evaluator', 'created_at')
    list_filter = ('institution', 'status', 'fee_paid')
    search_fields = ('student__student_id', 'student__user__first_name', 'marks_record__subject__name')
    raw_id_fields = ('student', 'marks_record', 'evaluator')

    @admin.display(description='Subject')
    def get_subject(self, obj):
        return obj.marks_record.subject.code
