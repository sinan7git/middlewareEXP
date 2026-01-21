from rest_framework import serializers
from .models import Event, Container, Quarantine, InvoiceReady
import re


class EventSerializer(serializers.Serializer):
    event_id = serializers.CharField(max_length=100)
    event_type = serializers.ChoiceField(choices=['GATE_IN', 'GATE_OUT', 'INSPECTION', 'WORK_ORDER'])
    container_no = serializers.CharField(max_length=11)
    owner_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    payload = serializers.DictField(required=False, default=dict)
    
    def validate_container_no(self, value):
        pattern = r'^[A-Z]{4}[0-9]{7}$'
        if not re.match(pattern, value.upper()):
            raise serializers.ValidationError(
                "Container number must be 4 letters + 7 digits (e.g., ABCD1234567)"
            )
        return value.upper()


class ContainerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Container
        fields = ['container_no', 'owner_code', 'status', 'last_event_id', 'updated_at']


class AuditSerializer(serializers.ModelSerializer):
    created_by = serializers.StringRelatedField()
    
    class Meta:
        model = Event
        fields = ['event_id', 'event_type', 'container_no', 'timestamp', 'payload', 'created_by']


class QuarantineSerializer(serializers.ModelSerializer):
    approved_by = serializers.StringRelatedField()
    
    class Meta:
        model = Quarantine
        fields = ['event_id', 'container_no', 'reason', 'status', 'event_data', 
                  'approved_by', 'approved_at', 'created_at']


class InvoiceReadySerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceReady
        fields = ['invoice_ref', 'container_no', 'work_order_id', 'amount', 
                  'currency', 'status', 'reason', 'retry_count', 'created_at']
