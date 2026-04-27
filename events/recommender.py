import pandas as pd
from collections import Counter
from sklearn.neighbors import NearestNeighbors
from .models import Event, Registration, Feedback


def get_recommendations(user, n_recommendations=3):
    """
    KNN-based recommender using both registrations and feedback ratings.
    - Registration counts as value 1
    - Feedback rating (1-5) overrides the registration value if present
    This means users get recommendations even if they never leave feedback.
    """

    # Get events the user already registered for (as a Python set)
    registered_ids = set(
        Registration.objects.filter(student=user).values_list('event_id', flat=True)
    )

    # ── COLD START: user has no registrations at all ──────────────────────────
    if not registered_ids:
        return list(
            Event.objects.order_by('-date')[:n_recommendations]
        )

    # ── BUILD USER-EVENT MATRIX from registrations ────────────────────────────
    # Start with all registrations, value = 1
    all_registrations = Registration.objects.select_related('student', 'event').all()
    data = {}
    for r in all_registrations:
        key = (r.student.id, r.event.id)
        data[key] = 1  # registered = 1

    # Override with actual rating if feedback exists (rating 1-5 is more informative)
    all_feedbacks = Feedback.objects.select_related('student', 'event').all()
    for f in all_feedbacks:
        key = (f.student.id, f.event.id)
        data[key] = f.rating  # rating overrides the default 1

    if not data:
        return list(
            Event.objects.exclude(id__in=registered_ids).order_by('-date')[:n_recommendations]
        )

    # Convert to DataFrame
    rows = [{'user_id': k[0], 'event_id': k[1], 'value': v} for k, v in data.items()]
    df = pd.DataFrame(rows)
    matrix = df.pivot_table(index='user_id', columns='event_id', values='value', fill_value=0)

    # ── COLD START: user not in matrix yet ────────────────────────────────────
    if user.id not in matrix.index:
        return list(
            Event.objects.exclude(id__in=registered_ids).order_by('-date')[:n_recommendations]
        )

    # ── FIT KNN ───────────────────────────────────────────────────────────────
    n_neighbors = min(6, len(matrix))  # +1 to account for self
    model = NearestNeighbors(n_neighbors=n_neighbors, metric='cosine', algorithm='brute')
    model.fit(matrix.values)

    user_index = matrix.index.get_loc(user.id)
    user_vector = matrix.iloc[user_index].values.reshape(1, -1)
    distances, indices = model.kneighbors(user_vector)

    # Exclude self from neighbours
    similar_user_ids = [
        matrix.index[i]
        for i in indices[0]
        if matrix.index[i] != user.id
    ][:5]

    if not similar_user_ids:
        return list(
            Event.objects.exclude(id__in=registered_ids).order_by('-date')[:n_recommendations]
        )

    # ── GET CATEGORY PREFERENCES from user's own registrations ───────────────
    preferred_categories = set(
        Event.objects.filter(id__in=registered_ids).values_list('category__name', flat=True)
    )

    # ── GET CANDIDATE EVENTS from similar users (registered OR rated highly) ──
    # Events similar users registered for
    neighbour_registered = list(
        Registration.objects.filter(
            student_id__in=similar_user_ids
        ).values_list('event_id', flat=True)
    )

    # Events similar users rated 4 or 5 (extra weight)
    neighbour_highly_rated = list(
        Feedback.objects.filter(
            student_id__in=similar_user_ids,
            rating__gte=4
        ).values_list('event_id', flat=True)
    )

    # Count appearances — highly rated events get counted twice (more weight)
    event_counts = Counter(neighbour_registered)
    for eid in neighbour_highly_rated:
        event_counts[eid] += 1  # extra +1 for high rating

    # ── SCORE EACH CANDIDATE ──────────────────────────────────────────────────
    scored = {}
    for event_id, count in event_counts.items():
        if event_id in registered_ids:
            continue  # skip events user already registered for
        try:
            event = Event.objects.get(id=event_id)
            category_bonus = 2 if event.category.name in preferred_categories else 0
            scored[event_id] = count + category_bonus
        except Event.DoesNotExist:
            pass

    # Sort by score descending
    ranked_ids = sorted(scored, key=scored.get, reverse=True)

    # ── BUILD RESULT LIST ─────────────────────────────────────────────────────
    recommended_events = []
    for eid in ranked_ids[:n_recommendations]:
        try:
            recommended_events.append(Event.objects.get(id=eid))
        except Event.DoesNotExist:
            pass

    # ── PAD WITH CATEGORY-MATCHED EVENTS if not enough results ───────────────
    if len(recommended_events) < n_recommendations and preferred_categories:
        existing_ids = set(e.id for e in recommended_events) | registered_ids
        extras = Event.objects.filter(
            category__name__in=preferred_categories
        ).exclude(id__in=existing_ids).order_by('-date')
        for event in extras:
            if len(recommended_events) >= n_recommendations:
                break
            recommended_events.append(event)

    # ── FINAL PAD with any remaining upcoming events ──────────────────────────
    if len(recommended_events) < n_recommendations:
        existing_ids = set(e.id for e in recommended_events) | registered_ids
        extras = Event.objects.exclude(id__in=existing_ids).order_by('-date')
        for event in extras:
            if len(recommended_events) >= n_recommendations:
                break
            recommended_events.append(event)

    return recommended_events