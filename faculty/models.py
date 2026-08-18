from django.db import models
from django.conf import settings
from tenants.models import TenantModel

class Faculty(TenantModel):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'
        ON_LEAVE = 'ON_LEAVE', 'On Leave'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='faculty_profile')
    employee_id = models.CharField(max_length=50)
    department = models.ForeignKey('academics.Department', on_delete=models.PROTECT, related_name='faculty')
    designation = models.CharField(max_length=100)  # e.g., Assistant Professor, HOD
    qualification = models.CharField(max_length=255, blank=True, null=True)
    joining_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.employee_id})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['institution', 'employee_id'], name='unique_employeeid_per_institution')
        ]

class FacultySubject(TenantModel):
    """
    Tracks which faculty member is allocated to teach a specific subject, section, and session.
    """
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='subject_allocations')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='faculty_allocations')
    section = models.ForeignKey('academics.Section', on_delete=models.CASCADE, null=True, blank=True, related_name='faculty_allocations')
    academic_session = models.ForeignKey('academics.AcademicSession', on_delete=models.CASCADE, related_name='faculty_allocations')
    allocated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        section_name = self.section.name if self.section else "All Sections"
        return f"{self.faculty.user.get_full_name()} -> {self.subject.name} ({section_name})"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['academic_session', 'subject', 'section'], 
                name='unique_subject_section_allocation_per_session'
            )
        ]
