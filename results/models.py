import uuid
from django.db import models
from django.conf import settings
from tenants.models import TenantModel

class Result(TenantModel):
    class Status(models.TextChoices):
        CALCULATED = 'CALCULATED', 'Calculated'
        REVIEWED = 'REVIEWED', 'HOD Reviewed'
        APPROVED = 'APPROVED', 'Controller Approved'
        PUBLISHED = 'PUBLISHED', 'Published (Visible to Student)'

    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='results')
    examination = models.ForeignKey('examinations.Examination', on_delete=models.CASCADE, related_name='results')
    semester = models.ForeignKey('academics.Semester', on_delete=models.CASCADE, related_name='results')
    academic_session = models.ForeignKey('academics.AcademicSession', on_delete=models.CASCADE, related_name='results')
    
    total_credits = models.PositiveIntegerField(default=0)
    earned_credits = models.PositiveIntegerField(default=0)
    sgpa = models.FloatField(default=0.0)
    cgpa = models.FloatField(default=0.0)
    percentage = models.FloatField(default=0.0)
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.CALCULATED)
    published_at = models.DateTimeField(blank=True, null=True)
    verification_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Result {self.student.student_id} - S{self.semester.number} ({self.status})"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'examination'], name='unique_student_result_per_exam')
        ]

class ResultSubject(models.Model):
    """
    Cached itemized snapshots of marks for each subject in the processed result card.
    """
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='subjects')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE)
    credits = models.PositiveIntegerField(default=4)
    
    # Snapshot marks
    internal_marks = models.FloatField(default=0.0)
    theory_marks = models.FloatField(default=0.0)
    practical_marks = models.FloatField(default=0.0)
    assignment_marks = models.FloatField(default=0.0)
    attendance_marks = models.FloatField(default=0.0)
    total_marks = models.FloatField(default=0.0)
    
    grade = models.CharField(max_length=10)
    grade_point = models.FloatField(default=0.0)
    is_pass = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.result.student.student_id} - {self.subject.code} ({self.grade})"

class ResultApproval(TenantModel):
    """
    Audit timeline records mapping verification and approval stages.
    """
    result = models.ForeignKey(Result, on_delete=models.CASCADE, related_name='approvals')
    role_acted = models.CharField(max_length=50)  # e.g., FACULTY, HOD, CONTROLLER
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status_before = models.CharField(max_length=50)
    status_after = models.CharField(max_length=50)
    comments = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Approval for {self.result.id} by {self.user.username}"
