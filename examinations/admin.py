from django.contrib import admin
from .models import Examination, ExamSubject, ExamRegistration


class ExamSubjectInline(admin.TabularInline):
    model = ExamSubject
    extra = 0
    fields = ('subject', 'exam_date', 'start_time', 'duration_minutes', 'max_marks', 'passing_marks')
    raw_id_fields = ('subject',)


@admin.register(Examination)
class ExaminationAdmin(admin.ModelAdmin):
    list_display = ('name', 'exam_type', 'program', 'semester', 'institution', 'status', 'start_date', 'end_date')
    list_filter = ('institution', 'status', 'exam_type', 'program')
    search_fields = ('name', 'program__name', 'program__code')
    raw_id_fields = ('academic_session', 'program', 'semester')
    ordering = ('-start_date',)
    inlines = [ExamSubjectInline]


@admin.register(ExamSubject)
class ExamSubjectAdmin(admin.ModelAdmin):
    list_display = ('subject', 'examination', 'exam_date', 'start_time', 'max_marks', 'passing_marks')
    list_filter = ('examination__institution', 'examination__program')
    search_fields = ('subject__name', 'subject__code', 'examination__name')
    raw_id_fields = ('examination', 'subject')


@admin.register(ExamRegistration)
class ExamRegistrationAdmin(admin.ModelAdmin):
    list_display = ('student', 'examination', 'institution', 'admit_card_generated', 'registration_date')
    list_filter = ('institution', 'admit_card_generated', 'examination')
    search_fields = ('student__student_id', 'student__user__first_name', 'examination__name')
    raw_id_fields = ('student', 'examination')
