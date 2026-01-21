from django.db import models
from django.contrib.auth.models import User


class Event(models.Model):
    EVENT_TYPES = [
        ('GATE_IN', 'Gate In'),
        ('GATE_OUT', 'Gate Out'),
        ('INSPECTION', 'Inspection'),
        ('WORK_ORDER', 'Work Order'),
    ]
    
    event_id = models.CharField(max_length=100, unique=True, primary_key=True)
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    container_no = models.CharField(max_length=11)
    timestamp = models.DateTimeField(auto_now_add=True)
    payload = models.JSONField(default=dict)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.event_id} - {self.event_type} - {self.container_no}"


class Container(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('GATE_IN', 'Gate In'),
        ('INSPECTED', 'Inspected'),
        ('WORK_DONE', 'Work Done'),
        ('GATE_OUT', 'Gate Out'),
    ]
    
    container_no = models.CharField(max_length=11, unique=True, primary_key=True)
    owner_code = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    last_event_id = models.CharField(max_length=100, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.container_no} - {self.status}"


class Quarantine(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    event_id = models.CharField(max_length=100, unique=True)
    container_no = models.CharField(max_length=11)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    event_data = models.JSONField(default=dict)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.event_id} - {self.status}"


class InvoiceReady(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SENT', 'Sent'),
        ('FAILED', 'Failed'),
    ]
    
    invoice_ref = models.CharField(max_length=100, unique=True, primary_key=True)
    container_no = models.CharField(max_length=11)
    work_order_id = models.CharField(max_length=100, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reason = models.TextField(blank=True, null=True)
    retry_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.invoice_ref} - {self.status}"


class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('operator', 'Operator'),
        ('finance_admin', 'Finance Admin'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='operator')
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"
