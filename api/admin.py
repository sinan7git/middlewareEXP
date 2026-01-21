from django.contrib import admin
from .models import Event, Container, Quarantine, InvoiceReady, UserProfile


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['event_id', 'event_type', 'container_no', 'timestamp', 'created_by']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['event_id', 'container_no']


@admin.register(Container)
class ContainerAdmin(admin.ModelAdmin):
    list_display = ['container_no', 'owner_code', 'status', 'last_event_id', 'updated_at']
    list_filter = ['status']
    search_fields = ['container_no', 'owner_code']


@admin.register(Quarantine)
class QuarantineAdmin(admin.ModelAdmin):
    list_display = ['event_id', 'container_no', 'reason', 'status', 'approved_by', 'created_at']
    list_filter = ['status']
    search_fields = ['event_id', 'container_no']


@admin.register(InvoiceReady)
class InvoiceReadyAdmin(admin.ModelAdmin):
    list_display = ['invoice_ref', 'container_no', 'amount', 'status', 'retry_count', 'created_at']
    list_filter = ['status']
    search_fields = ['invoice_ref', 'container_no']


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'role']
    list_filter = ['role']
