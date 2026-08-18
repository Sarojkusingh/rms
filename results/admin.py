from django.contrib import admin
from .models import Result, ResultSubject, ResultApproval


class ResultSubjectInline(admin.TabularInline):
    model = ResultSubject
    extra = 0
    fields = ('subject', 'credits', 'total_marks', 'grade', 'grade_point', 'is_pass')
    raw_id_fields = ('subject',)
    readonly_fields = ('subject', 'credits', 'total_marks', 'grade', 'grade_point', 'is_pass')
    can_delete = False


class ResultApprovalInline(admin.TabularInline):
    model = ResultApproval
    extra = 0
    fields = ('role_acted', 'user', 'status_before', 'status_after', 'comments', 'created_at')
    readonly_fields = ('created_at',)
    raw_id_fields = ('user',)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = (
        'get_student_id', 'examination', 'semester', 'institution',
        'sgpa', 'cgpa', 'percentage', 'status', 'published_at'
    )
    list_filter = ('institution', 'status', 'examination__program', 'semester')
    search_fields = ('student__student_id', 'student__user__first_name', 'student__user__last_name')
    raw_id_fields = ('student', 'examination', 'semester', 'academic_session')
    readonly_fields = ('verification_id',)
    ordering = ('-created_at',)
    inlines = [ResultSubjectInline, ResultApprovalInline]

    @admin.display(description='Student ID')
    def get_student_id(self, obj):
        return obj.student.student_id


@admin.register(ResultSubject)
class ResultSubjectAdmin(admin.ModelAdmin):
    list_display = ('result', 'subject', 'credits', 'total_marks', 'grade', 'grade_point', 'is_pass')
    list_filter = ('is_pass',)
    search_fields = ('result__student__student_id', 'subject__name', 'subject__code')
    raw_id_fields = ('result', 'subject')


@admin.register(ResultApproval)
class ResultApprovalAdmin(admin.ModelAdmin):
    list_display = ('result', 'role_acted', 'user', 'institution', 'status_before', 'status_after', 'created_at')
    list_filter = ('institution', 'role_acted', 'status_after')
    search_fields = ('user__username', 'result__student__student_id')
    raw_id_fields = ('result', 'user')
