from django.core.management.base import BaseCommand
from accounts.models import CustomUser
from events.models import Event, Registration, Feedback
import random

class Command(BaseCommand):
    help = 'Seed fake student data for KNN testing'

    def handle(self, *args, **kwargs):
        events = list(Event.objects.all())
        if not events:
            self.stdout.write('No events found. Add events first.')
            return

        # Define student preference profiles
        profiles = [
            {'name': 'alice_smith',   'interests': ['Tech', 'Careers']},
            {'name': 'bob_jones',     'interests': ['Sports', 'Social']},
            {'name': 'carol_white',   'interests': ['Careers', 'Social']},
            {'name': 'david_brown',   'interests': ['Tech', 'Sports']},
            {'name': 'eve_taylor',    'interests': ['Social', 'Careers']},
            {'name': 'frank_lee',     'interests': ['Tech', 'Social']},
            {'name': 'grace_hall',    'interests': ['Careers', 'Tech']},
            {'name': 'henry_clark',   'interests': ['Sports', 'Careers']},
            {'name': 'iris_adams',    'interests': ['Social', 'Tech']},
            {'name': 'jack_wilson',   'interests': ['Tech', 'Careers']},
            {'name': 'kate_martin',   'interests': ['Sports', 'Social']},
            {'name': 'liam_moore',    'interests': ['Careers', 'Tech']},
        ]

        created_count = 0
        for profile in profiles:
            user, created = CustomUser.objects.get_or_create(
                username=profile['name'],
                defaults={
                    'email': f"{profile['name']}@university.ac.uk",
                    'role': 'student',
                    'first_name': profile['name'].split('_')[0].capitalize(),
                    'last_name': profile['name'].split('_')[1].capitalize(),
                }
            )
            if created:
                user.set_password('testpass123')
                user.save()
                created_count += 1

            # Register and give feedback for matching events
            for event in events:
                category_name = event.category.name if event.category else ''
                if category_name in profile['interests']:
                    reg, _ = Registration.objects.get_or_create(
                        student=user,
                        event=event,
                        defaults={'status': 'registered'}
                    )
                    # Give high rating for preferred category
                    rating = random.randint(4, 5)
                    Feedback.objects.get_or_create(
                        student=user,
                        event=event,
                        defaults={'rating': rating, 'comment': ''}
                    )
                elif random.random() < 0.2:
                    # Sometimes register for non-preferred events with lower rating
                    reg, _ = Registration.objects.get_or_create(
                        student=user,
                        event=event,
                        defaults={'status': 'registered'}
                    )
                    rating = random.randint(2, 3)
                    Feedback.objects.get_or_create(
                        student=user,
                        event=event,
                        defaults={'rating': rating, 'comment': ''}
                    )

        self.stdout.write(f'Done! Created {created_count} new students with registrations and feedback.')