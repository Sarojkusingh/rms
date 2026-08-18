from django.db import models
from tenants.models import Institution, TenantModel

class Plan(models.Model):
    name = models.CharField(max_length=100)  # e.g., Starter, Growth, Professional, Enterprise
    student_limit = models.PositiveIntegerField(default=500)
    faculty_limit = models.PositiveIntegerField(default=50)
    storage_limit_gb = models.PositiveIntegerField(default=10)
    admin_limit = models.PositiveIntegerField(default=5)
    
    price_monthly = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    price_yearly = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    features = models.JSONField(default=list, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Subscription(TenantModel):
    class BillingCycle(models.TextChoices):
        MONTHLY = 'MONTHLY', 'Monthly'
        YEARLY = 'YEARLY', 'Yearly'

    class Status(models.TextChoices):
        TRIAL = 'TRIAL', 'Trial Mode'
        ACTIVE = 'ACTIVE', 'Active Paid'
        PAST_DUE = 'PAST_DUE', 'Past Due / Unpaid'
        CANCELED = 'CANCELED', 'Canceled'
        SUSPENDED = 'SUSPENDED', 'Suspended'

    # Overwrite TenantModel relationship to make it OneToOne
    institution = models.OneToOneField(Institution, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    billing_cycle = models.CharField(max_length=20, choices=BillingCycle.choices, default=BillingCycle.MONTHLY)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.TRIAL)
    
    start_date = models.DateField()
    end_date = models.DateField()
    next_billing_date = models.DateField()
    is_trial = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.institution.name} - {self.plan.name} ({self.status})"

class Usage(TenantModel):
    # Overwrite to make it OneToOne
    institution = models.OneToOneField(Institution, on_delete=models.CASCADE, related_name='usage')
    current_students = models.PositiveIntegerField(default=0)
    current_faculty = models.PositiveIntegerField(default=0)
    current_storage_bytes = models.BigIntegerField(default=0)
    current_admins = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Usage for {self.institution.name}"

    @property
    def storage_gb(self):
        return round(self.current_storage_bytes / (1024 * 1024 * 1024), 2)
