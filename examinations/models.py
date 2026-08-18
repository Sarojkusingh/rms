from django.db import models
from tenants.models import TenantModel

class Examination(TenantModel):
    class ExamType(models.TextChoices):
        INTERNAL = 'INTERNAL', 'Internal Assessment'
        MID_SEM = 'MID_SEM', 'Mid Semester'
        END_SEM = 'END_SEM', 'End Semester'
        PRACTICAL = 'PRACTICAL', 'Practical Examination'
        VIVA = 'VIVA', 'Viva Voce'
        SUPPLEMENTARY = 'SUPPLEMENTARY', 'Supplementary Examination'
        REVALUATION = 'REVALUATION', 'Revaluation evaluation'

    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ACTIVE = 'ACTIVE', 'Active (Open for Reg)'
        ONGOING = 'ONGOING', 'Ongoing Exams'
        COMPLETED = 'COMPLETED', 'Exams Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'

    name = models.CharField(max_length=255)
    exam_type = models.CharField(max_length=30, choices=ExamType.choices, default=ExamType.END_SEM)
    academic_session = models.ForeignKey('academics.AcademicSession', on_delete=models.CASCADE, related_name='examinations')
    program = models.ForeignKey('academics.Program', on_delete=models.CASCADE, related_name='examinations')
    semester = models.ForeignKey('academics.Semester', on_delete=models.CASCADE, related_name='examinations')
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.program.code} S{self.semester.number}"

class ExamSubject(models.Model):
    """
    Sub-schedule linking specific subjects within an examination.
    """
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='exam_subjects')
    subject = models.ForeignKey('academics.Subject', on_delete=models.CASCADE, related_name='exam_schedules')
    exam_date = models.DateField()
    start_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField(default=180)
    max_marks = models.PositiveIntegerField(default=100)
    passing_marks = models.PositiveIntegerField(default=40)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.subject.code} in {self.examination.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['examination', 'subject'], name='unique_subject_per_examination')
        ]

class ExamRegistration(TenantModel):
    """
    Tracks which student is registered to sit for a specific examination.
    """
    student = models.ForeignKey('students.Student', on_delete=models.CASCADE, related_name='exam_registrations')
    examination = models.ForeignKey(Examination, on_delete=models.CASCADE, related_name='registrations')
    registration_date = models.DateTimeField(auto_now_add=True)
    admit_card_generated = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.student_id} registered for {self.examination.name}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['student', 'examination'], name='unique_student_registration_per_exam')
        ]
