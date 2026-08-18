from django.db import models
from django.conf import settings
from tenants.models import TenantModel

class Student(TenantModel):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        SUSPENDED = 'SUSPENDED', 'Suspended'
        COMPLETED = 'COMPLETED', 'Completed'
        ALUMNI = 'ALUMNI', 'Alumni'

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='student')
    student_id = models.CharField(max_length=50)  # e.g., Roll / Reg number
    registration_number = models.CharField(max_length=100, blank=True, null=True)
    dob = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    father_name = models.CharField(max_length=255, blank=True, null=True)
    mother_name = models.CharField(max_length=255, blank=True, null=True)
    parent_contact = models.CharField(max_length=20, blank=True, null=True)
    
    # Current Academic Mappings
    department = models.ForeignKey('academics.Department', on_delete=models.PROTECT, related_name='students')
    program = models.ForeignKey('academics.Program', on_delete=models.PROTECT, related_name='students')
    semester = models.ForeignKey('academics.Semester', on_delete=models.PROTECT, related_name='students')
    section = models.ForeignKey('academics.Section', on_delete=models.PROTECT, null=True, blank=True, related_name='students')
    academic_session = models.ForeignKey('academics.AcademicSession', on_delete=models.PROTECT, related_name='students')
    
    photo = models.ImageField(upload_to='student_photos/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_id})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['institution', 'student_id'], name='unique_studentid_per_institution')
        ]

class Enrollment(models.Model):
    """
    Tracks historical enrollment records of a student per semester and session.
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    academic_session = models.ForeignKey('academics.AcademicSession', on_delete=models.PROTECT)
    semester = models.ForeignKey('academics.Semester', on_delete=models.PROTECT)
    section = models.ForeignKey('academics.Section', on_delete=models.PROTECT, null=True, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.student_id} - Semester {self.semester.number} ({self.academic_session.name})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'semester', 'academic_session'], name='unique_student_semester_session')
        ]

class StudentAcademicHistory(models.Model):
    """
    Stores aggregate metrics for marksheets and transcripts.
    """
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name='academic_history')
    cgpa = models.FloatField(default=0.0)
    total_credits_completed = models.PositiveIntegerField(default=0)
    active_backlogs = models.PositiveIntegerField(default=0)
    cleared_backlogs = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"History for {self.student.student_id} (CGPA: {self.cgpa})"
