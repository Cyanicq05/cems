import datetime
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import CustomUser
from .models import Event, Category, Registration, Feedback


class CEMSTestCase(TestCase):

    def setUp(self):
        """Set up test data used across all tests."""
        self.client = Client()

        # Create a student user
        self.student = CustomUser.objects.create_user(
            username='teststudent',
            password='testpass123',
            role='student'
        )

        # Create an admin user
        self.admin = CustomUser.objects.create_user(
            username='testadmin',
            password='testpass123',
            role='admin'
        )

        # Create a category
        self.category = Category.objects.create(name='Tech')

        # Create an upcoming event
        self.event = Event.objects.create(
            title='Python Workshop',
            description='Learn Python basics.',
            category=self.category,
            date=datetime.date.today() + datetime.timedelta(days=10),
            time=datetime.time(10, 0),
            venue='Lab 1',
            capacity=30,
            created_by=self.admin
        )

        # Create a past event
        self.past_event = Event.objects.create(
            title='Old Tech Talk',
            description='A past event.',
            category=self.category,
            date=datetime.date.today() - datetime.timedelta(days=5),
            time=datetime.time(10, 0),
            venue='Hall A',
            capacity=50,
            created_by=self.admin
        )


# ─────────────────────────────────────────────
# TEST 1: Student can register successfully
# ─────────────────────────────────────────────
class TestStudentRegistration(CEMSTestCase):

    def test_student_can_register_for_event(self):
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.post(reverse('register_event', args=[self.event.id]))
        self.assertEqual(Registration.objects.filter(
            student=self.student, event=self.event, status='registered'
        ).count(), 1)


# ─────────────────────────────────────────────
# TEST 2: Duplicate registration is prevented
# ─────────────────────────────────────────────
class TestDuplicateRegistration(CEMSTestCase):

    def test_duplicate_registration_not_created(self):
        self.client.login(username='teststudent', password='testpass123')
        # Register twice
        self.client.post(reverse('register_event', args=[self.event.id]))
        self.client.post(reverse('register_event', args=[self.event.id]))
        # Should only have one registration record
        self.assertEqual(Registration.objects.filter(
            student=self.student, event=self.event
        ).count(), 1)


# ─────────────────────────────────────────────
# TEST 3: Registration blocked for past events
# ─────────────────────────────────────────────
class TestPastEventRegistration(CEMSTestCase):

    def test_cannot_register_for_past_event(self):
        self.client.login(username='teststudent', password='testpass123')
        self.client.post(reverse('register_event', args=[self.past_event.id]))
        # No registration should be created
        self.assertEqual(Registration.objects.filter(
            student=self.student, event=self.past_event
        ).count(), 0)


# ─────────────────────────────────────────────
# TEST 4: Admin cannot register for events
# ─────────────────────────────────────────────
class TestAdminCannotRegister(CEMSTestCase):

    def test_admin_cannot_register_for_event(self):
        self.client.login(username='testadmin', password='testpass123')
        self.client.post(reverse('register_event', args=[self.event.id]))
        self.assertEqual(Registration.objects.filter(
            student=self.admin, event=self.event
        ).count(), 0)


# ─────────────────────────────────────────────
# TEST 5: Student can cancel a registration
# ─────────────────────────────────────────────
class TestCancelRegistration(CEMSTestCase):

    def test_student_can_cancel_registration(self):
        self.client.login(username='teststudent', password='testpass123')
        reg = Registration.objects.create(
            student=self.student, event=self.event, status='registered'
        )
        self.client.post(reverse('cancel_registration', args=[reg.id]))
        reg.refresh_from_db()
        self.assertEqual(reg.status, 'cancelled')


# ─────────────────────────────────────────────
# TEST 6: Student can submit feedback
# ─────────────────────────────────────────────
class TestFeedbackSubmission(CEMSTestCase):

    def test_student_can_submit_feedback(self):
        self.client.login(username='teststudent', password='testpass123')
        # Must have a registration first
        Registration.objects.create(
            student=self.student, event=self.event, status='registered'
        )
        self.client.post(reverse('leave_feedback', args=[self.event.id]), {
            'rating': 4,
            'comment': 'Great event!'
        })
        self.assertEqual(Feedback.objects.filter(
            student=self.student, event=self.event
        ).count(), 1)


# ─────────────────────────────────────────────
# TEST 7: Feedback blocked without registration
# ─────────────────────────────────────────────
class TestFeedbackWithoutRegistration(CEMSTestCase):

    def test_feedback_blocked_without_registration(self):
        self.client.login(username='teststudent', password='testpass123')
        # No registration created — feedback should be blocked
        self.client.post(reverse('leave_feedback', args=[self.event.id]), {
            'rating': 5,
            'comment': 'Should not work.'
        })
        self.assertEqual(Feedback.objects.filter(
            student=self.student, event=self.event
        ).count(), 0)


# ─────────────────────────────────────────────
# TEST 8: Admin pages blocked for students
# ─────────────────────────────────────────────
class TestAdminAccessControl(CEMSTestCase):

    def test_student_cannot_access_admin_dashboard(self):
        self.client.login(username='teststudent', password='testpass123')
        response = self.client.get(reverse('admin_dashboard'))
        # Should redirect away, not show the admin page
        self.assertRedirects(response, reverse('student_dashboard'))