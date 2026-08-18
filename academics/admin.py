from django.contrib import admin
from .models import AcademicSession, Department, Program, Course, Semester, Subject, Section


@admin.register(AcademicSession)
class AcademicSessionAdmin(admin.ModelAdmin):
    list_display = ('name', 'institution', 'is_active', 'created_at')
    list_filter = ('is_active', 'institution')
    search_fields = ('name', 'institution__name')
    ordering = ('-created_at',)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'institution', 'created_at')
    list_filter = ('institution',)
    search_fields = ('name', 'code', 'institution__name')


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'department', 'institution', 'duration_years', 'created_at')
    list_filter = ('institution', 'department')
    search_fields = ('name', 'code')
    raw_id_fields = ('department',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'program', 'institution', 'created_at')
    list_filter = ('institution',)
    search_fields = ('name', 'program__name')
    raw_id_fields = ('program',)


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('number', 'program', 'institution', 'created_at')
    list_filter = ('institution', 'program')
    search_fields = ('program__name', 'program__code')
    raw_id_fields = ('program',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'program', 'semester', 'credits', 'is_elective', 'institution')
    list_filter = ('institution', 'is_elective', 'program')
    search_fields = ('name', 'code')
    raw_id_fields = ('program', 'semester')


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'program', 'semester', 'institution', 'created_at')
    list_filter = ('institution', 'program')
    search_fields = ('name',)
    raw_id_fields = ('program', 'semester')
