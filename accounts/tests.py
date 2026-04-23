from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser


class UserRegistrationTest(TestCase):

    def setUp(self):
        self.client = Client()

    # ─────────────────────────────────────────────
    # TEST 1: User can register successfully
    # ─────────────────────────────────────────────
    def test_user_can_register(self):
        self.client.post(reverse('register'), {
            'full_name': 'Test Student',
            'username': 'newstudent',
            'email': 'newstudent@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(CustomUser.objects.filter(username='newstudent').count(), 1)

    # ─────────────────────────────────────────────
    # TEST 2: Duplicate username is blocked
    # ─────────────────────────────────────────────
    def test_duplicate_username_blocked(self):
        CustomUser.objects.create_user(username='existinguser', password='pass123')
        self.client.post(reverse('register'), {
            'full_name': 'Another User',
            'username': 'existinguser',
            'email': 'another@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(CustomUser.objects.filter(username='existinguser').count(), 1)

    # ─────────────────────────────────────────────
    # TEST 3: Duplicate email is blocked
    # ─────────────────────────────────────────────
    def test_duplicate_email_blocked(self):
        CustomUser.objects.create_user(
            username='firstuser', email='same@test.com', password='pass123'
        )
        self.client.post(reverse('register'), {
            'full_name': 'Second User',
            'username': 'seconduser',
            'email': 'same@test.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
        })
        self.assertEqual(CustomUser.objects.filter(email='same@test.com').count(), 1)

    # ─────────────────────────────────────────────
    # TEST 4: Login works with correct credentials
    # ─────────────────────────────────────────────
    def test_login_with_correct_credentials(self):
        CustomUser.objects.create_user(
            username='loginuser', password='testpass123', role='student'
        )
        response = self.client.post(reverse('login'), {
            'username': 'loginuser',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)

    # ─────────────────────────────────────────────
    # TEST 5: Login fails with wrong password
    # ─────────────────────────────────────────────
    def test_login_fails_with_wrong_password(self):
        CustomUser.objects.create_user(
            username='loginuser2', password='correctpass'
        )
        response = self.client.post(reverse('login'), {
            'username': 'loginuser2',
            'password': 'wrongpassword',
        })
        self.assertNotEqual(response.status_code, 302)

    # ─────────────────────────────────────────────
    # TEST 6: New user is assigned student role by default
    # ─────────────────────────────────────────────
    def test_new_user_has_student_role(self):
        user = CustomUser.objects.create_user(
            username='studentrole', password='pass123'
        )
        self.assertEqual(user.role, 'student')