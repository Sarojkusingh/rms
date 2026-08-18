from django.db import models
from django.conf import settings
from tenants.models import TenantModel

class Marks(TenantModel):
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft Saved'
        SUBMITTED = 'SUBMITTED', 'Submitted to HOD'
        APPROVED = 'APPROVED', 'Approved by HOD'
        REJECTED = 'REJECTED', 'Rejected / Needs Correction'
        LOCKED = 'LOCKED', 'Locked by Exam Cell'

    exam_registration = models.ForeignKey(
        'examinations.ExamRegistration', 
        on_delete=models.CASCADE, 
        related_name='marks'
    )
    subject = models.ForeignKey(
        'academics.Subject', 
        on_delete=models.CASCADE, 
        related_name='marks'
    )
    
    # Split Marks Components
    internal_marks = models.FloatField(default=0.0)
    theory_marks = models.FloatField(default=0.0)
    practical_marks = models.FloatField(default=0.0)
    assignment_marks = models.FloatField(default=0.0)
    attendance_marks = models.FloatField(default=0.0)
    
    # Aggregated Values
    total_marks = models.FloatField(default=0.0)
    grade = models.CharField(max_length=10, blank=True, null=True)
    grade_point = models.FloatField(default=0.0)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    entered_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='entered_marks'
    )
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.exam_registration.student.student_id} - {self.subject.code}: {self.total_marks}"

    def calculate_total(self):
        self.total_marks = (
            self.internal_marks + 
            self.theory_marks + 
            self.practical_marks + 
            self.assignment_marks + 
            self.attendance_marks
        )
        return self.total_marks

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['exam_registration', 'subject'], name='unique_marks_per_registration_subject')
        ]
        verbose_name_plural = "Marks"
