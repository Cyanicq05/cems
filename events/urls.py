from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.browse_events, name='browse_events'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('events/<int:event_id>/register/',
         views.register_event, name='register_event'),
    path('events/<int:event_id>/feedback/',
         views.leave_feedback, name='leave_feedback'),
    path('my-registrations/', views.my_registrations, name='my_registrations'),
    path('registrations/<int:reg_id>/cancel/',
         views.cancel_registration, name='cancel_registration'),
    path('recommendations/', views.recommendations, name='recommendations'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/events/create/', views.event_create, name='event_create'),
    path('dashboard/events/<int:event_id>/edit/',
         views.event_edit, name='event_edit'),
    path('dashboard/events/<int:event_id>/delete/',
         views.event_delete, name='event_delete'),
    path('dashboard/', views.student_dashboard, name='student_dashboard'),
    path('my-feedback/', views.my_feedback, name='my_feedback'),
    path('profile/', views.my_profile, name='my_profile'),
    path('calendar/', views.calendar_view, name='calendar_view'),
    path('admin-calendar/', views.admin_calendar, name='admin_calendar'),
]
