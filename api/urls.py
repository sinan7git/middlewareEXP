from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health'),
    
    path('events/', views.post_event, name='post_event'),
    path('containers/<str:container_no>/', views.get_container, name='get_container'),
    path('audit/<str:container_no>/', views.get_audit, name='get_audit'),
    
    path('quarantine/', views.list_quarantine, name='list_quarantine'),
    path('quarantine/<str:event_id>/approve/', views.approve_quarantine_event, name='approve_quarantine'),
    
    path('replay/<str:container_no>/', views.replay_container_events, name='replay_container'),
    
    path('invoices/', views.list_invoices, name='list_invoices'),
    path('invoices/<str:invoice_ref>/send/', views.send_invoice, name='send_invoice'),
]
