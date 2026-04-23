from django.contrib import admin
from .models import Category, Event, Registration, Feedback, Recommendation

admin.site.register(Category)
admin.site.register(Event)
admin.site.register(Registration)
admin.site.register(Feedback)
admin.site.register(Recommendation)