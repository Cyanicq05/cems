from django.core.management.base import BaseCommand
from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Creates or resets the default admin user'

    def handle(self, *args, **kwargs):
        if not CustomUser.objects.filter(username='admin').exists():
            u = CustomUser.objects.create_user(username='admin', password='Admin1234!')
            u.role = 'admin'
            u.is_staff = True
            u.is_superuser = True
            u.save()
            self.stdout.write('Admin created!')
        else:
            u = CustomUser.objects.get(username='admin')
            u.set_password('Admin1234!')
            u.role = 'admin'
            u.is_staff = True
            u.is_superuser = True
            u.save()
            self.stdout.write('Admin password reset!')