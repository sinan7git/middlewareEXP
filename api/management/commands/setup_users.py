from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from api.models import UserProfile


class Command(BaseCommand):
    help = 'Create test users with tokens'

    def handle(self, *args, **options):
        operator, created = User.objects.get_or_create(
            username='operator1',
            defaults={'email': 'operator@test.com'}
        )
        if created:
            operator.set_password('operator123')
            operator.save()
        
        UserProfile.objects.get_or_create(user=operator, defaults={'role': 'operator'})
        op_token, _ = Token.objects.get_or_create(user=operator)
        
        admin, created = User.objects.get_or_create(
            username='finance_admin1',
            defaults={'email': 'admin@test.com'}
        )
        if created:
            admin.set_password('admin123')
            admin.save()
        
        UserProfile.objects.get_or_create(user=admin, defaults={'role': 'finance_admin'})
        admin_token, _ = Token.objects.get_or_create(user=admin)
        
        self.stdout.write(self.style.SUCCESS('\n=== USERS CREATED ==='))
        self.stdout.write(f'Operator Token:      {op_token.key}')
        self.stdout.write(f'Finance Admin Token: {admin_token.key}')
