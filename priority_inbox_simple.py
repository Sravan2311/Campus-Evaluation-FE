import heapq
import datetime
import json
import urllib.request

def get_api_notifications(url, auth_token=None):
    """Fetch notifications from API endpoint."""
    try:
        request = urllib.request.Request(url)
        request.add_header("Accept", "application/json")
        if auth_token:
            request.add_header("Authorization", f"Bearer {auth_token}")
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode())
        return data.get("notifications", data) if isinstance(data, dict) else data
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        try:
            error_body = e.read().decode()
            print(f"Response: {error_body}")
        except:
            pass
        return []
    except Exception as e:
        print(f"Error fetching API: {e}")
        return []

def parse_timestamp(ts):
    """Convert timestamp string to datetime."""
    if isinstance(ts, datetime.datetime):
        return ts
    if isinstance(ts, str):
        try:
            return datetime.datetime.fromisoformat(ts.replace('Z', '+00:00'))
        except:
            return datetime.datetime.utcnow()
    return datetime.datetime.utcnow()

def score_notification(notif):
    """Calculate priority score for a notification."""
    placement_scores = {"banner": 5, "alert": 4, "email": 3, "message": 2, "summary": 1}
    result_scores = {"success": 4, "warning": 3, "info": 2, "fail": 1}
    event_scores = {"deadline": 5, "emergency": 4, "meeting": 3, "reminder": 2, "social": 1}
    
    placement = placement_scores.get(notif.get("placement", "summary"), 1)
    result = result_scores.get(notif.get("result", "info"), 1)
    event = event_scores.get(notif.get("event", "social"), 1)
    
    # Recency: newer is better
    ts = parse_timestamp(notif.get("timestamp"))
    age_hours = max(0, (datetime.datetime.utcnow() - ts).total_seconds() / 3600)
    recency = 1.0 / (1.0 + age_hours)
    
    return placement * 0.35 + result * 0.25 + event * 0.25 + recency * 1.5

def top_notifications(notifications, n=10):
    """Get top N unread notifications by priority."""
    heap = []
    for notif in notifications:
        if notif.get("read"):
            continue
        score = score_notification(notif)
        if len(heap) < n:
            heapq.heappush(heap, (score, notif))
        elif score > heap[0][0]:
            heapq.heapreplace(heap, (score, notif))
    
    return sorted(heap, key=lambda x: x[0], reverse=True)

def main():
    url = "http://4.224.186.213/evaluation-service/notifications"
    notifications = get_api_notifications(url)
    
    if not notifications:
        print("No notifications found")
        return
    
    top_10 = top_notifications(notifications, 10)
    
    print("Top 10 Priority Notifications:\n")
    for i, (score, notif) in enumerate(top_10, 1):
        title = notif.get("title", "Untitled")
        print(f"{i}. {title} (score: {score:.2f})")
    
    # Save to JSON
    with open("top_notifications.json", "w") as f:
        json.dump([notif for _, notif in top_10], f, indent=2, default=str)
    print("\nSaved to top_notifications.json")

if __name__ == "__main__":
    main()
