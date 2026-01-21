from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from .models import Event, Container, Quarantine, InvoiceReady
from .serializers import (
    EventSerializer, ContainerSerializer, AuditSerializer,
    QuarantineSerializer, InvoiceReadySerializer
)
from .permissions import IsOperator, IsFinanceAdmin
from .services import (
    process_event, send_to_erp, replay_container, approve_quarantine
)
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsOperator])
def post_event(request):
    serializer = EventSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'success': False, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    result = process_event(serializer.validated_data, request.user)
    
    if result.get('success'):
        return Response(result, status=status.HTTP_201_CREATED)
    elif result.get('quarantined'):
        return Response(result, status=status.HTTP_202_ACCEPTED)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsOperator])
def get_container(request, container_no):

    try:
        container = Container.objects.get(container_no=container_no.upper())
        serializer = ContainerSerializer(container)
        return Response(serializer.data)
    except Container.DoesNotExist:
        return Response(
            {'error': 'Container not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsOperator])
def get_audit(request, container_no):

    events = Event.objects.filter(container_no=container_no.upper())
    
    if not events:
        return Response(
            {'error': 'No events found for container'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    serializer = AuditSerializer(events, many=True)
    return Response({
        'container_no': container_no.upper(),
        'event_count': events.count(),
        'events': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsFinanceAdmin])
def approve_quarantine_event(request, event_id):
    result = approve_quarantine(event_id, request.user)
    
    if result.get('success'):
        return Response(result)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsOperator])
def list_quarantine(request):
    quarantined = Quarantine.objects.all().order_by('-created_at')
    serializer = QuarantineSerializer(quarantined, many=True)
    return Response({
        'count': quarantined.count(),
        'items': serializer.data
    })


@api_view(['POST'])
@permission_classes([IsOperator])
def replay_container_events(request, container_no):
    result = replay_container(container_no.upper())
    
    if result.get('success'):
        return Response(result)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsFinanceAdmin])
def send_invoice(request, invoice_ref):
    result = send_to_erp(invoice_ref)
    
    if result.get('success'):
        return Response(result)
    else:
        return Response(result, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsOperator])
def list_invoices(request):
    invoices = InvoiceReady.objects.all().order_by('-created_at')
    serializer = InvoiceReadySerializer(invoices, many=True)
    return Response({
        'count': invoices.count(),
        'items': serializer.data
    })


@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok'})
