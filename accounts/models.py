from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        SUPER_ADMIN = 'SUPER_ADMIN', 'Super Admin'
        INSTITUTION_OWNER = 'INSTITUTION_OWNER', 'Institution Owner'
        INSTITUTION_ADMIN = 'INSTITUTION_ADMIN', 'Institution Admin'
        EXAM_CONTROLLER = 'EXAM_CONTROLLER', 'Examination Controller'
        HOD = 'HOD', 'Head of Department'
        FACULTY = 'FACULTY', 'Faculty'
        STUDENT = 'STUDENT', 'Student'

    role = models.CharField(max_length=30, choices=Role.choices, default=Role.STUDENT)
    institution = models.ForeignKey(
        'tenants.Institution',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN or self.is_superuser

    @property
    def is_institution_admin(self):
        return self.role in [self.Role.INSTITUTION_OWNER, self.Role.INSTITUTION_ADMIN]

    @property
    def is_exam_controller(self):
        return self.role == self.Role.EXAM_CONTROLLER

    @property
    def is_hod(self):
        return self.role == self.Role.HOD

    @property
    def is_faculty_role(self):
        return self.role == self.Role.FACULTY

    @property
    def is_student_role(self):
        return self.role == self.Role.STUDENT
