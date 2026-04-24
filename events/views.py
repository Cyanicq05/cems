import datetime
from accounts.models import CustomUser
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Event, Registration, Feedback, Category


def browse_events(request):
    events = Event.objects.all()
    categories = Category.objects.all()

    search_query = request.GET.get('search', '').strip()
    if search_query:
        events = events.filter(title__icontains=search_query)

    selected_category = request.GET.get('category', '').strip()
    if selected_category:
        events = events.filter(category__name=selected_category)

    return render(request, 'student/events.html', {
        'events': events,
        'categories': categories,
        'search_query': search_query,
        'selected_category': selected_category,
    })


def event_detail(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    is_registered = False
    recommended_events = []
    if request.user.is_authenticated:
        is_registered = Registration.objects.filter(
            student=request.user, event=event, status='registered'
        ).exists()
        from .recommender import get_recommendations
        recommended_events = get_recommendations(request.user, n_recommendations=3)
    return render(request, 'student/event_detail.html', {
        'event': event,
        'is_registered': is_registered,
        'recommended_events': recommended_events,
        'today': datetime.date.today(),
    })


@login_required(login_url='/login/')
def register_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    if request.user.role == 'admin':
        return redirect('admin_dashboard')

    if event.date < datetime.date.today():
        messages.error(request, 'Sorry, this event has already passed and is no longer open for registration.')
        return redirect('event_detail', event_id=event_id)

    active_count = Registration.objects.filter(event=event, status='registered').count()
    if active_count >= event.capacity:
        messages.error(request, 'Sorry, this event is already full.')
        return redirect('event_detail', event_id=event_id)

    reg, created = Registration.objects.get_or_create(
        student=request.user,
        event=event,
        defaults={'status': 'registered'}
    )
    if not created and reg.status == 'cancelled':
        reg.status = 'registered'
        reg.save()

    messages.success(request, 'You have successfully registered for this event.')
    return redirect('my_registrations')


@login_required(login_url='/login/')
def my_registrations(request):
    registrations = Registration.objects.filter(student=request.user)
    active_count = registrations.filter(status='registered').count()
    cancelled_count = registrations.filter(status='cancelled').count()
    return render(request, 'student/registrations.html', {
        'registrations': registrations,
        'active_count': active_count,
        'cancelled_count': cancelled_count,
    })


@login_required(login_url='/login/')
def cancel_registration(request, reg_id):
    reg = get_object_or_404(Registration, id=reg_id, student=request.user)
    reg.status = 'cancelled'
    reg.save()
    messages.success(request, 'Your registration has been cancelled.')
    return redirect('my_registrations')


@login_required(login_url='/login/')
def leave_feedback(request, event_id):
    event = get_object_or_404(Event, id=event_id)

    has_registration = Registration.objects.filter(
        student=request.user, event=event
    ).exists()
    if not has_registration:
        return redirect('my_registrations')

    submitted = False
    if request.method == 'POST':
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '')

        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, TypeError):
            return render(request, 'student/feedback_form.html', {
                'event': event,
                'error': 'Please select a rating between 1 and 5.',
                'submitted': False,
            })

        Feedback.objects.update_or_create(
            student=request.user,
            event=event,
            defaults={'rating': rating, 'comment': comment}
        )
        messages.success(request, 'Your feedback has been submitted. Thank you!')
        submitted = True

    return render(request, 'student/feedback_form.html', {'event': event, 'submitted': submitted})


@login_required(login_url='/login/')
def my_feedback(request):
    feedbacks = Feedback.objects.filter(student=request.user).select_related('event')
    return render(request, 'student/feedback.html', {'feedbacks': feedbacks})


@login_required(login_url='/login/')
def recommendations(request):
    from .recommender import get_recommendations
    recommended_events = get_recommendations(request.user)
    return render(request, 'student/recommendations.html', {'recommended_events': recommended_events})


@login_required(login_url='/login/')
def student_dashboard(request):
    from .recommender import get_recommendations
    registrations = Registration.objects.filter(student=request.user, status='registered')
    feedback_count = Feedback.objects.filter(student=request.user).count()
    recommended_events = get_recommendations(request.user, n_recommendations=3)
    context = {
        'registrations': registrations,
        'registered_count': registrations.count(),
        'feedback_count': feedback_count,
        'recommended_events': recommended_events,
    }
    return render(request, 'student/dashboard.html', context)


@login_required(login_url='/login/')
def my_profile(request):
    return render(request, 'student/profile.html')


@login_required(login_url='/login/')
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('student_dashboard')

    today = datetime.date.today()

    # Build enriched event list with extra stats
    all_events = Event.objects.all().order_by('date')
    event_stats = []
    for event in all_events:
        reg_count = Registration.objects.filter(event=event, status='registered').count()
        feedback_count = Feedback.objects.filter(event=event).count()
        remaining = event.capacity - reg_count
        event_stats.append({
            'event': event,
            'reg_count': reg_count,
            'feedback_count': feedback_count,
            'remaining': remaining,
            'is_past': event.date < today,
        })

    context = {
        'event_stats': event_stats,
        'total_events': Event.objects.count(),
        'total_registrations': Registration.objects.filter(status='registered').count(),
        'total_feedback': Feedback.objects.count(),
        'total_students': CustomUser.objects.filter(role='student').count(),
        'recent_registrations': Registration.objects.order_by('-registered_at')[:5],
        'upcoming_events_count': Event.objects.filter(date__gte=today).count(),
    }
    return render(request, 'admin/dashboard.html', context)


@login_required(login_url='/login/')
def event_create(request):
    from .models import Category

    if request.user.role != 'admin':
        return redirect('student_dashboard')

    if request.method == 'POST':
        Event.objects.create(
            title=request.POST.get('title'),
            description=request.POST.get('description'),
            category=Category.objects.get(id=request.POST.get('category')),
            date=request.POST.get('date'),
            time=request.POST.get('time'),
            venue=request.POST.get('venue'),
            capacity=request.POST.get('capacity'),
            created_by=request.user,
        )
        messages.success(request, 'Event created successfully.')
        return redirect('admin_dashboard')
    return render(request, 'admin/event_create.html', {'categories': Category.objects.all()})


@login_required(login_url='/login/')
def event_edit(request, event_id):
    from .models import Category

    if request.user.role != 'admin':
        return redirect('student_dashboard')

    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        event.title = request.POST.get('title')
        event.description = request.POST.get('description')
        event.category = Category.objects.get(id=request.POST.get('category'))
        event.date = request.POST.get('date')
        event.time = request.POST.get('time')
        event.venue = request.POST.get('venue')
        event.capacity = request.POST.get('capacity')
        event.save()
        messages.success(request, 'Event updated successfully.')
        return redirect('admin_dashboard')
    return render(request, 'admin/event_edit.html', {'event': event, 'categories': Category.objects.all()})


@login_required(login_url='/login/')
def event_delete(request, event_id):
    if request.user.role != 'admin':
        return redirect('student_dashboard')

    event = get_object_or_404(Event, id=event_id)
    if request.method == 'POST':
        event.delete()
        messages.success(request, 'Event deleted successfully.')
    return redirect('admin_dashboard')

# Add this import at the top of views.py (with your other imports):
# import calendar as cal_module

# Add this view to views.py:

@login_required(login_url='/login/')
def calendar_view(request):
    import calendar as cal_module

    today = datetime.date.today()
    month = int(request.GET.get('month', today.month))
    year = int(request.GET.get('year', today.year))

    # Handle month overflow
    if month > 12:
        month = 1
        year += 1
    if month < 1:
        month = 12
        year -= 1

    # Get all events this month
    events_this_month = Event.objects.filter(date__year=year, date__month=month)

    # Get student's registrations this month
    my_registrations = Registration.objects.filter(
        student=request.user,
        event__date__year=year,
        event__date__month=month,
        status='registered'
    ).select_related('event')

    registered_event_ids = set(r.event.id for r in my_registrations)

    # Build calendar days
    cal = cal_module.monthcalendar(year, month)
    calendar_days = []

    # Get first weekday of month and number of days
    first_weekday, num_days = cal_module.monthrange(year, month)

    # Build flat list of days (Mon=0 start)
    # Pad start
    start_pad = first_weekday  # Monday=0
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    prev_month_days = cal_module.monthrange(prev_year, prev_month)[1]

    all_days = []

    # Previous month padding
    for i in range(start_pad):
        day_num = prev_month_days - start_pad + i + 1
        all_days.append({
            'day': day_num,
            'in_month': False,
            'is_today': False,
            'events': [],
            'date': datetime.date(prev_year, prev_month, day_num),
        })

    # Current month days
    for d in range(1, num_days + 1):
        date = datetime.date(year, month, d)
        day_events = []
        for event in events_this_month:
            if event.date == date:
                day_events.append({
                    'id': event.id,
                    'title': event.title,
                    'is_registered': event.id in registered_event_ids,
                })
        all_days.append({
            'day': d,
            'in_month': True,
            'is_today': date == today,
            'events': day_events,
            'date': date,
        })

    # Next month padding to complete grid (multiple of 7)
    remainder = len(all_days) % 7
    if remainder != 0:
        next_month = month + 1 if month < 12 else 1
        next_year = year if month < 12 else year + 1
        for i in range(1, 7 - remainder + 1):
            all_days.append({
                'day': i,
                'in_month': False,
                'is_today': False,
                'events': [],
                'date': datetime.date(next_month if next_month <= 12 else 1, next_month if next_month <= 12 else 1, i),
            })

    # Prev/next month nav
    prev_month_nav = month - 1 if month > 1 else 12
    prev_year_nav = year if month > 1 else year - 1
    next_month_nav = month + 1 if month < 12 else 1
    next_year_nav = year if month < 12 else year + 1

    month_name = datetime.date(year, month, 1).strftime('%B')

    context = {
        'calendar_days': all_days,
        'month_name': month_name,
        'year': year,
        'prev_month': prev_month_nav,
        'prev_year': prev_year_nav,
        'next_month': next_month_nav,
        'next_year': next_year_nav,
        'available_events': events_this_month.order_by('date'),
        'registered_this_month': my_registrations.order_by('event__date'),
    }
    return render(request, 'student/calendar.html', context)

# Add this view to events/views.py

@login_required(login_url='/login/')
def student_dashboard(request):
    from .recommender import get_recommendations
    registrations = Registration.objects.filter(student=request.user, status='registered')
    feedback_count = Feedback.objects.filter(student=request.user).count()
    recommended_events = get_recommendations(request.user, n_recommendations=3)

    # Fallback for new users: show upcoming popular events by registration count
    is_new_user = not recommended_events
    if is_new_user:
        from django.db.models import Count
        recommended_events = Event.objects.filter(
            date__gte=datetime.date.today()
        ).annotate(
            reg_count=Count('registration')
        ).order_by('-reg_count')[:3]

    context = {
        'registrations': registrations,
        'registered_count': registrations.count(),
        'feedback_count': feedback_count,
        'recommended_events': recommended_events,
        'is_new_user': is_new_user,
    }
    return render(request, 'student/dashboard.html', context)