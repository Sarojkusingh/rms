from django.db import models
from django.conf import settings
from tenants.models import TenantModel

class Backlog(TenantModel):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active Backlog'
        CLEARED = 'CLEARED', 'Cleared / Passed'
        PENDING = 'PENDING', 'Pending Examination'

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='backlogs')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='backlogs')
    semester = models.ForeignKey('academics.Semester', on_delete=models.CASCADE, related_name='backlogs')
    attempt_number = models.PositiveIntegerField(default=1)
    marks_obtained = models.FloatField(default=0.0)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    cleared_in_examination = models.ForeignKey(
        'examinations.Examination', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='cleared_backlogs'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.student_id} - {self.subject.code} ({self.status})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'subject', 'status'], name='unique_active_backlog_per_subject', condition=models.Q(status='ACTIVE'))
        ]

class RevaluationApplication(TenantModel):
    class Status(models.TextChoices):
        APPLIED = 'APPLIED', 'Applied'
        UNDER_REVIEW = 'UNDER_REVIEW', 'Under Review'
        EVALUATED = 'EVALUATED', 'Evaluated'
        COMPLETED = 'COMPLETED', 'Completed / Published'

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='revaluation_applications')
    marks_record = models.ForeignKey('marks.Marks', on_delete=models.CASCADE, related_name='revaluation_applications')
    reason = models.TextField(blank=True, null=True)
    fee_paid = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    
    old_marks = models.FloatField(default=0.0)
    new_marks = models.FloatField(default=0.0)
    evaluator = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='evaluated_revaluations'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Revaluation: {self.student.student_id} - {self.marks_record.subject.code}"
