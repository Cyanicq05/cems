import pandas as pd
from collections import Counter
from sklearn.neighbors import NearestNeighbors
from .models import Event, Registration, Feedback


def get_recommendations(user, n_recommendations=3):
    """
    KNN-based recommender using both registrations and feedback ratings.
    - Registration counts as value 1
    - Feedback rating (1-5) overrides the registration value if present
    - Category bonus is weighted by how many times the user registered in that category
      e.g. 3x Sports = higher bonus than 1x Social
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
    all_registrations = Registration.objects.select_related('student', 'event').all()
    data = {}
    for r in all_registrations:
        key = (r.student.id, r.event.id)
        data[key] = 1  # registered = 1

    # Override with actual rating if feedback exists
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

    # ── GET CATEGORY PREFERENCES weighted by frequency ───────────────────────
    # e.g. if user registered for Sports 3 times and Social 1 time:
    # category_freq = {'Sports': 3, 'Social': 1}
    user_categories = list(
        Event.objects.filter(id__in=registered_ids).values_list('category__name', flat=True)
    )
    category_freq = Counter(user_categories)  # {'Sports': 3, 'Social': 1}
    max_freq = max(category_freq.values()) if category_freq else 1
    preferred_categories = set(category_freq.keys())

    # ── GET CANDIDATE EVENTS from similar users ───────────────────────────────
    neighbour_registered = list(
        Registration.objects.filter(
            student_id__in=similar_user_ids
        ).values_list('event_id', flat=True)
    )

    neighbour_highly_rated = list(
        Feedback.objects.filter(
            student_id__in=similar_user_ids,
            rating__gte=4
        ).values_list('event_id', flat=True)
    )

    event_counts = Counter(neighbour_registered)
    for eid in neighbour_highly_rated:
        event_counts[eid] += 1  # extra +1 for high rating

    # ── SCORE EACH CANDIDATE ──────────────────────────────────────────────────
    # Category bonus is proportional to how often user registered in that category
    # e.g. Sports (3 times) → bonus = (3/3) * 4 = 4.0
    #      Social (1 time)  → bonus = (1/3) * 4 = 1.3
    #      Career (0 times) → bonus = 0
    scored = {}
    for event_id, count in event_counts.items():
        if event_id in registered_ids:
            continue  # skip already registered
        try:
            event = Event.objects.get(id=event_id)
            freq = category_freq.get(event.category.name, 0)
            category_bonus = (freq / max_freq) * 4  # max bonus = 4 for top category
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

    # ── PAD WITH CATEGORY-MATCHED EVENTS weighted by frequency ───────────────
    if len(recommended_events) < n_recommendations and preferred_categories:
        existing_ids = set(e.id for e in recommended_events) | registered_ids
        # Order padding by most-registered category first
        top_categories = [cat for cat, _ in category_freq.most_common()]
        for cat in top_categories:
            if len(recommended_events) >= n_recommendations:
                break
            extras = Event.objects.filter(
                category__name=cat
            ).exclude(id__in=existing_ids).order_by('-date')
            for event in extras:
                if len(recommended_events) >= n_recommendations:
                    break
                recommended_events.append(event)
                existing_ids.add(event.id)

    # ── FINAL PAD with any remaining events ──────────────────────────────────
    if len(recommended_events) < n_recommendations:
        existing_ids = set(e.id for e in recommended_events) | registered_ids
        extras = Event.objects.exclude(id__in=existing_ids).order_by('-date')
        for event in extras:
            if len(recommended_events) >= n_recommendations:
                break
            recommended_events.append(event)

    return recommended_events