import random
import uuid
import logging
from decimal import Decimal
from django.utils import timezone
from .models import Event, Container, Quarantine, InvoiceReady

logger = logging.getLogger(__name__)

STATUS_FLOW = {
    'PENDING': ['GATE_IN'],
    'GATE_IN': ['INSPECTED'],
    'INSPECTED': ['WORK_DONE'],
    'WORK_DONE': ['GATE_OUT'],
    'GATE_OUT': [],
}

EVENT_TO_STATUS = {
    'GATE_IN': 'GATE_IN',
    'INSPECTION': 'INSPECTED',
    'WORK_ORDER': 'WORK_DONE',
    'GATE_OUT': 'GATE_OUT',
}


def validate_status_progression(current_status, event_type):
    new_status = EVENT_TO_STATUS.get(event_type)
    if not new_status:
        return False, f"Unknown event type: {event_type}"
    
    allowed = STATUS_FLOW.get(current_status, [])
    if new_status not in allowed:
        return False, f"Cannot go from {current_status} to {new_status}. Allowed: {allowed}"
    
    return True, None


def check_duplicate_event(event_id):
    return Event.objects.filter(event_id=event_id).exists()


def check_duplicate_work_order(work_order_id):
    return InvoiceReady.objects.filter(work_order_id=work_order_id).exists()


def send_to_quarantine(event_id, container_no, reason, event_data):
    Quarantine.objects.create(
        event_id=event_id,
        container_no=container_no,
        reason=reason,
        event_data=event_data,
        status='PENDING'
    )
    logger.warning(f"Event {event_id} quarantined: {reason}")


def process_event(validated_data, user):

    event_id = validated_data['event_id']
    event_type = validated_data['event_type']
    container_no = validated_data['container_no']
    owner_code = validated_data.get('owner_code', '')
    payload = validated_data.get('payload', {})
    
    if check_duplicate_event(event_id):
        return {'success': False, 'error': 'Duplicate event_id', 'quarantined': False}
    
    container, created = Container.objects.get_or_create(
        container_no=container_no,
        defaults={'owner_code': owner_code, 'status': 'PENDING'}
    )
    
    valid, error = validate_status_progression(container.status, event_type)
    if not valid:
        send_to_quarantine(event_id, container_no, error, validated_data)
        return {'success': False, 'error': error, 'quarantined': True}
    
    if event_type == 'GATE_IN' and not owner_code:
        send_to_quarantine(event_id, container_no, 'Missing owner_code', validated_data)
        return {'success': False, 'error': 'Missing owner_code', 'quarantined': True}
    
    if owner_code and container.owner_code and owner_code != container.owner_code:
        send_to_quarantine(event_id, container_no, 
                          f'Owner conflict: {owner_code} vs {container.owner_code}', 
                          validated_data)
        return {'success': False, 'error': 'Owner conflict', 'quarantined': True}
    
    if event_type == 'WORK_ORDER':
        work_order_id = payload.get('work_order_id', event_id)
        if check_duplicate_work_order(work_order_id):
            return {'success': False, 'error': 'Work order already billed', 'quarantined': False}
    
    event = Event.objects.create(
        event_id=event_id,
        event_type=event_type,
        container_no=container_no,
        payload=payload,
        created_by=user
    )
    
    container.status = EVENT_TO_STATUS[event_type]
    container.last_event_id = event_id
    if owner_code:
        container.owner_code = owner_code
    container.save()
    
    logger.info(f"Event {event_id} processed. Container {container_no} -> {container.status}")
    
    invoice_result = None
    if event_type == 'WORK_ORDER':
        work_order_id = payload.get('work_order_id', event_id)
        amount = Decimal(payload.get('amount', '100.00'))
        invoice_result = create_invoice(container_no, work_order_id, amount)
    
    return {
        'success': True, 
        'event_id': event_id, 
        'new_status': container.status,
        'invoice': invoice_result
    }


def create_invoice(container_no, work_order_id, amount):
    invoice_ref = f"INV-{uuid.uuid4().hex[:8].upper()}"
    invoice = InvoiceReady.objects.create(
        invoice_ref=invoice_ref,
        container_no=container_no,
        work_order_id=work_order_id,
        amount=amount,
        currency='USD',
        status='PENDING'
    )
    logger.info(f"Invoice {invoice_ref} created for {container_no}")
    return {'invoice_ref': invoice_ref, 'status': 'PENDING'}


def send_to_erp(invoice_ref):
    try:
        invoice = InvoiceReady.objects.get(invoice_ref=invoice_ref)
    except InvoiceReady.DoesNotExist:
        return {'success': False, 'error': 'Invoice not found'}

    if invoice.status == 'SENT':
        return {
            'success': False,
            'error': 'Invoice already sent to ERP',
            'invoice_ref': invoice_ref,
            'sent_at': invoice.updated_at.isoformat()
        }
    
    max_retries = 3
    
    while invoice.retry_count < max_retries:
        invoice.retry_count += 1
        invoice.save()
        
        if random.random() > 0.3:
            invoice.status = 'SENT'
            invoice.reason = 'Successfully sent to ERP'
            invoice.save()
            logger.info(f"Invoice {invoice_ref} sent to ERP (attempt {invoice.retry_count})")
            return {'success': True, 'attempts': invoice.retry_count}
        
        logger.warning(f"ERP send failed for {invoice_ref} (attempt {invoice.retry_count})")
    
    invoice.status = 'FAILED'
    invoice.reason = f'Failed after {max_retries} attempts'
    invoice.save()
    logger.error(f"Invoice {invoice_ref} FAILED after {max_retries} attempts")
    return {'success': False, 'error': invoice.reason, 'attempts': invoice.retry_count}


def replay_container(container_no):

    events = Event.objects.filter(container_no=container_no).order_by('timestamp')
    
    if not events:
        return {'success': False, 'error': 'No events found'}
    
    container, _ = Container.objects.get_or_create(
        container_no=container_no,
        defaults={'status': 'PENDING'}
    )
    container.status = 'PENDING'
    container.owner_code = None
    container.last_event_id = None
    
    replayed = []
    for event in events:
        new_status = EVENT_TO_STATUS.get(event.event_type)
        if new_status:
            container.status = new_status
            container.last_event_id = event.event_id
            owner = event.payload.get('owner_code')
            if owner:
                container.owner_code = owner
            replayed.append({
                'event_id': event.event_id,
                'event_type': event.event_type,
                'status': new_status
            })
    
    container.save()
    logger.info(f"Replayed {len(replayed)} events for {container_no}")
    
    return {
        'success': True,
        'container_no': container_no,
        'final_status': container.status,
        'events_replayed': len(replayed),
        'details': replayed
    }


def approve_quarantine(event_id, user):
    try:
        quarantine = Quarantine.objects.get(event_id=event_id, status='PENDING')
    except Quarantine.DoesNotExist:
        return {'success': False, 'error': 'Quarantine record not found or already processed'}
    
    quarantine.status = 'APPROVED'
    quarantine.approved_by = user
    quarantine.approved_at = timezone.now()
    quarantine.save()
    
    event_data = quarantine.event_data
    event_type = event_data['event_type']
    container_no = event_data['container_no']
    owner_code = event_data.get('owner_code', '')
    payload = event_data.get('payload', {})
    
    event = Event.objects.create(
        event_id=event_id,
        event_type=event_type,
        container_no=container_no,
        payload=payload,
        created_by=user
    )
    
    container, _ = Container.objects.get_or_create(
        container_no=container_no,
        defaults={'status': 'PENDING'}
    )
    container.status = EVENT_TO_STATUS.get(event_type, container.status)
    container.last_event_id = event_id
    if owner_code:
        container.owner_code = owner_code
    container.save()
    
    logger.info(f"Quarantine {event_id} approved by {user.username}")
    
    return {
        'success': True,
        'event_id': event_id,
        'new_status': container.status,
        'approved_by': user.username
    }
