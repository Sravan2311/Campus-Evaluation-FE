# Stage 1

## Priority Inbox Design

### Goal
Build a notification priority inbox that always displays the top `n` unread notifications by importance and recency. The system should keep the top notifications updated efficiently as new notifications arrive.

### Approach

1. Priority scoring:
   - `placement` is the strongest signal because where the notification appears reflects its importance.
   - `result` is the second signal because success/warning/failure affects user urgency.
   - `event` is the third signal because the type of activity influences relevance.
   - `recency` is added so newer notifications are favored over older ones when importance is similar.

2. Score formula:
   - `placement_weight * 0.35`
   - `result_weight * 0.25`
   - `event_weight * 0.25`
   - `recency_score * 1.5`

3. Top-N maintenance:
   - Use a fixed-size min-heap of capacity `n`.
   - For each unread notification, compute a priority score and push it into the heap.
   - If the heap grows beyond capacity, remove the smallest score.
   - This keeps the highest `n` notifications in `O(log n)` per insertion.

### Why this is efficient

- A min-heap of size `n` provides the top `n` items in streaming fashion without sorting the entire dataset every time.
- For each new notification, insertion and conditional replacement cost `O(log n)`.
- The heap naturally handles continuous arrival of notifications by preserving just the strongest candidates.
- This is much better than sorting all unread notifications repeatedly, especially when the unread pool is large.

## Implementation details

### Notification representation
Each notification includes:
- `id`
- `title`
- `placement` (banner, alert, email, message, summary)
- `result` (success, warning, info, fail)
- `event` (deadline, emergency, meeting, reminder, social)
- `timestamp`
- `read` flag

### Score components

- `placement`: differentiates high-visibility messages from low-priority summaries.
- `result`: assigns more weight to warnings, failures, and successes than plain information.
- `event`: gives highest priority to deadlines and emergencies.
- `recency`: modeled as `1 / (1 + age_hours)` so a notification’s urgency decays smoothly over time.

### Real-time maintenance strategy

- For a live system, each incoming notification is evaluated with the same score function.
- If a notification is marked read, it is excluded from the priority inbox.
- The top-N heap is updated immediately, ensuring the inbox view remains fresh.
- Older notifications naturally fall out of the top-N when newer, higher-priority notifications arrive.

## How to run

1. Run `python priority_notifications.py`.
2. The script prints the top 10 notifications.
3. It also writes `top_notifications.json` and, if Pillow is available, `priority_notifications_output.png`.

## Extensibility

- Add user-specific weights for placement or event categories.
- Adjust recency decay for different notification lifetimes.
- Store notifications in a streaming queue and compute priority on ingestion.
- Use a separate fast-access cache for the current inbox view.

## Outcome

This solution delivers a functioning Python implementation that computes the top 10 unread notifications and keeps the inbox efficient as new notifications arrive. It is ready to be expanded into a full notification service with persistence and live delivery.
