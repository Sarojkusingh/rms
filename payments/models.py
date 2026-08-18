from django.db import models
from tenants.models import TenantModel

class Payment(TenantModel):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESS = 'SUCCESS', 'Successful'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'

    subscription = models.ForeignKey(
        'subscriptions.Subscription', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='payments'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default='CARD')  # e.g., CARD, UPI, NETBANKING
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    transaction_id = models.CharField(max_length=100, unique=True)
    
    # Billing / GST details
    org_name = models.CharField(max_length=255, blank=True, null=True)
    gstin = models.CharField(max_length=15, blank=True, null=True)
    billing_address = models.TextField(blank=True, null=True)
    billing_state = models.CharField(max_length=100, blank=True, null=True)
    billing_pin = models.CharField(max_length=10, blank=True, null=True)
    
    invoice_pdf = models.FileField(upload_to='invoices/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment {self.transaction_id} - {self.amount} ({self.status})"
