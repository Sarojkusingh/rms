from django.db import models
from tenants.models import TenantModel

class AcademicSession(TenantModel):
    name = models.CharField(max_length=50)  # e.g., "2025-2026", "Fall 2025"
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.institution.name})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['institution', 'name'], name='unique_session_per_institution')
        ]

class Department(TenantModel):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)  # e.g., "CSE", "ECE"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['institution', 'code'], name='unique_department_code_per_institution')
        ]

class Program(TenantModel):
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programs')
    name = models.CharField(max_length=255)  # e.g., "B.Tech in Computer Science"
    code = models.CharField(max_length=20)  # e.g., "BTECH-CSE"
    duration_years = models.PositiveIntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['institution', 'code'], name='unique_program_code_per_institution')
        ]

class Course(TenantModel):
    # Represents the overall syllabus / curriculum version or cohort mapping
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=255)  # e.g., "Computer Science Curriculum 2025"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Semester(TenantModel):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='semesters')
    number = models.PositiveIntegerField()  # e.g., 1, 2, 3, 4...
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Semester {self.number} - {self.program.code}"

    class Meta:
        ordering = ['number']
        constraints = [
            models.UniqueConstraint(fields=['program', 'number'], name='unique_semester_number_per_program')
        ]

class Subject(TenantModel):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='subjects')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='subjects')
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=20)  # e.g., "CS-301"
    credits = models.PositiveIntegerField(default=4)
    is_elective = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.code})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['program', 'code'], name='unique_subject_code_per_program')
        ]

class Section(TenantModel):
    program = models.ForeignKey(Program, on_delete=models.CASCADE, related_name='sections')
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE, related_name='sections')
    name = models.CharField(max_length=50)  # e.g., "Section A", "Section B"
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.program.code} S{self.semester.number})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['semester', 'name'], name='unique_section_name_per_semester')
        ]
