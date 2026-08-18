from django.db import models

class Institution(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='institution_logos/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class InstitutionSettings(models.Model):
    class ResultPolicy(models.TextChoices):
        PERCENTAGE = 'PERCENTAGE', 'Percentage-based'
        CGPA = 'CGPA', 'GPA/CGPA-based'

    institution = models.OneToOneField(Institution, on_delete=models.CASCADE, related_name='settings')
    current_session = models.ForeignKey(
        'academics.AcademicSession', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='+'
    )
    # Default grading system mapping: letter grade to grade point value
    grading_system = models.JSONField(default=dict, blank=True)
    passing_marks = models.PositiveIntegerField(default=40)
    result_policy = models.CharField(
        max_length=20, 
        choices=ResultPolicy.choices, 
        default=ResultPolicy.PERCENTAGE
    )
    onboarding_step = models.PositiveIntegerField(default=1)
    is_onboarded = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settings for {self.institution.name}"

    def save(self, *args, **kwargs):
        # Default grading system if empty
        if not self.grading_system:
            self.grading_system = {
                'A+': 10,
                'A': 9,
                'B+': 8,
                'B': 7,
                'C': 6,
                'D': 5,
                'F': 0
            }
        super().save(*args, **kwargs)

class TenantManager(models.Manager):
    pass

class TenantModel(models.Model):
    institution = models.ForeignKey(
        Institution, 
        on_delete=models.CASCADE,
        related_name="%(app_label)s_%(class)s_related"
    )

    objects = TenantManager()

    class Meta:
        abstract = True

