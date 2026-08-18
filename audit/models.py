from django.db import models
from django.conf import settings
from tenants.models import Institution

class AuditLog(models.Model):
    # Optional institution (Super Admin actions do not belong to an institution)
    institution = models.ForeignKey(
        Institution, 
        on_delete=models.CASCADE, 
        related_name='audit_logs',
        null=True, 
        blank=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='audit_logs'
    )
    user_role = models.CharField(max_length=50, blank=True, null=True)
    action = models.CharField(max_length=255)  # e.g., "Faculty changed Mathematics marks from 72 to 78."
    module = models.CharField(max_length=100)  # e.g., "MARKS", "RESULTS", "ACADEMICS"
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        user_str = self.user.username if self.user else "System"
        return f"[{self.timestamp}] {user_str} ({self.user_role}): {self.action}"
