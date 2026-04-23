from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    STUDENT = 'student'
    ADMIN = 'admin'
    ROLE_CHOICES = [
        (STUDENT, 'Student'),
        (ADMIN, 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=STUDENT)

    def __str__(self):
        return f"{self.username} ({self.role})"