from django.core.management.base import BaseCommand
from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Creates the default admin user'

    def handle(self, *args, **kwargs):
        if not CustomUser.objects.filter(username='admin').exists():
            u = CustomUser.objects.create_user(username='admin', password='Admin1234!')
            u.role = 'admin'
            u.is_staff = True
            u.is_superuser = True
            u.save()
            self.stdout.write('Admin created!')
        else:
            self.stdout.write('Admin already exists.')