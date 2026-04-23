import pandas as pd
import numpy as np
from sklearn.neighbors import NearestNeighbors
from .models import Event, Registration, Feedback


def get_recommendations(user, n_recommendations=3):
    """
    KNN-based event recommender.
    Finds similar students based on their feedback ratings,
    then recommends events those students liked that the current user hasn't registered for.
    """

    # Step 1: Get all feedback data
    feedbacks = Feedback.objects.select_related('student', 'event').all()

    if not feedbacks.exists():
        return Event.objects.none()

    # Step 2: Build a user-event rating matrix
    data = []
    for f in feedbacks:
        data.append({
            'user_id': f.student.id,
            'event_id': f.event.id,
            'rating': f.rating
        })

    df = pd.DataFrame(data)

    if df.empty:
        return Event.objects.none()

    # Pivot table: rows = users, columns = events, values = ratings
    matrix = df.pivot_table(index='user_id', columns='event_id', values='rating', fill_value=0)

    # Step 3: Check if current user is in the matrix
    if user.id not in matrix.index:
        # User has no feedback yet — return popular events they haven't registered for
        registered_ids = Registration.objects.filter(
            student=user
        ).values_list('event_id', flat=True)
        return Event.objects.exclude(id__in=registered_ids)[:n_recommendations]

    # Step 4: Fit KNN model
    n_neighbors = min(5, len(matrix))
    model = NearestNeighbors(n_neighbors=n_neighbors, metric='cosine', algorithm='brute')
    model.fit(matrix.values)

    # Step 5: Find similar users
    user_index = matrix.index.get_loc(user.id)
    user_vector = matrix.iloc[user_index].values.reshape(1, -1)
    distances, indices = model.kneighbors(user_vector)

    # Step 6: Get events the similar users rated highly (4 or 5)
    similar_user_ids = [matrix.index[i] for i in indices[0] if matrix.index[i] != user.id]

    candidate_event_ids = Feedback.objects.filter(
        student_id__in=similar_user_ids,
        rating__gte=4
    ).values_list('event_id', flat=True)

    # Step 7: Remove events the current user already registered for
    registered_ids = Registration.objects.filter(
        student=user
    ).values_list('event_id', flat=True)

    recommended_ids = [
        eid for eid in candidate_event_ids
        if eid not in list(registered_ids)
    ]

    # Remove duplicates while preserving order
    seen = set()
    unique_ids = []
    for eid in recommended_ids:
        if eid not in seen:
            seen.add(eid)
            unique_ids.append(eid)

    # Step 8: Return recommended Event objects
    recommended_events = []
    for eid in unique_ids[:n_recommendations]:
        try:
            recommended_events.append(Event.objects.get(id=eid))
        except Event.DoesNotExist:
            pass

    return recommended_events