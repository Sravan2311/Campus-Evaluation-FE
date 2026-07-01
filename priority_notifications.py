import heapq
import datetime
import json
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from typing import List, Optional

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = None
    ImageDraw = None
    ImageFont = None


@dataclass(order=True)
class PrioritizedNotification:
    sort_index: float = field(init=False)
    score: float = field(compare=False)
    notification: dict = field(compare=False)

    def __post_init__(self):
        self.sort_index = self.score


class PriorityInbox:
    """Maintains the top N most important unread notifications."""

    PLACEMENT_WEIGHT = {
        "banner": 5.0,
        "alert": 4.0,
        "email": 3.0,
        "message": 2.0,
        "summary": 1.0,
    }
    RESULT_WEIGHT = {
        "success": 4.0,
        "warning": 3.0,
        "info": 2.0,
        "fail": 1.0,
    }
    EVENT_WEIGHT = {
        "deadline": 5.0,
        "emergency": 4.0,
        "meeting": 3.0,
        "reminder": 2.0,
        "social": 1.0,
    }

    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        self.heap: List[PrioritizedNotification] = []

    def _normalize(self, value: float, min_value: float, max_value: float) -> float:
        if max_value <= min_value:
            return 0.0
        return (value - min_value) / (max_value - min_value)

    def _recency_score(self, timestamp: datetime.datetime, now: Optional[datetime.datetime] = None) -> float:
        now = now or datetime.datetime.utcnow()
        age_seconds = max(0.0, (now - timestamp).total_seconds())
        age_hours = age_seconds / 3600.0
        # More recent notifications get higher recency score; older notifications decay.
        return 1.0 / (1.0 + age_hours)

    def _importance_score(self, notification: dict, now: Optional[datetime.datetime] = None) -> float:
        placement = notification.get("placement", "summary")
        result = notification.get("result", "info")
        event = notification.get("event", "social")
        timestamp = notification.get("timestamp")

        placement_score = self.PLACEMENT_WEIGHT.get(placement, 1.0)
        result_score = self.RESULT_WEIGHT.get(result, 1.0)
        event_score = self.EVENT_WEIGHT.get(event, 1.0)
        recency_score = self._recency_score(timestamp, now)

        return (
            placement_score * 0.35
            + result_score * 0.25
            + event_score * 0.25
            + recency_score * 1.5
        )

    def add_notification(self, notification: dict, now: Optional[datetime.datetime] = None) -> None:
        if notification.get("read", False):
            return

        score = self._importance_score(notification, now)
        entry = PrioritizedNotification(score=score, notification=notification)

        if len(self.heap) < self.capacity:
            heapq.heappush(self.heap, entry)
        else:
            if score > self.heap[0].score:
                heapq.heapreplace(self.heap, entry)

    def top_notifications(self) -> List[dict]:
        return [item.notification for item in sorted(self.heap, key=lambda x: x.score, reverse=True)]

    def snapshot(self) -> str:
        rows = ["Top {} Priority Notifications:".format(self.capacity)]
        for index, notification in enumerate(self.top_notifications(), 1):
            rows.append(
                f"{index}. [{notification['timestamp'].isoformat()}] {notification['title']}"
                f" (placement={notification['placement']}, result={notification['result']}, event={notification['event']}, score={self._importance_score(notification):.3f})"
            )
        return "\n".join(rows)


def build_sample_notifications() -> List[dict]:
    now = datetime.datetime.utcnow()
    sample_data = [
        {"id": 1, "title": "Final exam schedule updated", "placement": "banner", "result": "info", "event": "deadline", "timestamp": now - datetime.timedelta(hours=1), "read": False},
        {"id": 2, "title": "Fire drill tomorrow at 9 AM", "placement": "alert", "result": "warning", "event": "emergency", "timestamp": now - datetime.timedelta(hours=2), "read": False},
        {"id": 3, "title": "New assignment posted for CS101", "placement": "email", "result": "info", "event": "deadline", "timestamp": now - datetime.timedelta(hours=4), "read": False},
        {"id": 4, "title": "Sports fest registration deadline", "placement": "summary", "result": "warning", "event": "deadline", "timestamp": now - datetime.timedelta(days=1), "read": False},
        {"id": 5, "title": "Guest lecture on AI starts in 30 minutes", "placement": "banner", "result": "info", "event": "meeting", "timestamp": now - datetime.timedelta(minutes=20), "read": False},
        {"id": 6, "title": "Lab session canceled", "placement": "email", "result": "fail", "event": "meeting", "timestamp": now - datetime.timedelta(hours=5), "read": False},
        {"id": 7, "title": "Your fee payment is due", "placement": "alert", "result": "warning", "event": "deadline", "timestamp": now - datetime.timedelta(hours=8), "read": False},
        {"id": 8, "title": "Cafeteria menu updated", "placement": "summary", "result": "info", "event": "social", "timestamp": now - datetime.timedelta(hours=3), "read": False},
        {"id": 9, "title": "Counseling session tomorrow", "placement": "message", "result": "info", "event": "meeting", "timestamp": now - datetime.timedelta(hours=12), "read": False},
        {"id": 10, "title": "Hackathon team matching open", "placement": "email", "result": "info", "event": "social", "timestamp": now - datetime.timedelta(hours=10), "read": False},
        {"id": 11, "title": "Network maintenance at midnight", "placement": "alert", "result": "warning", "event": "reminder", "timestamp": now - datetime.timedelta(hours=6), "read": False},
        {"id": 12, "title": "Results published for last semester", "placement": "banner", "result": "success", "event": "info", "timestamp": now - datetime.timedelta(hours=15), "read": False},
        {"id": 13, "title": "Library books due tomorrow", "placement": "email", "result": "warning", "event": "deadline", "timestamp": now - datetime.timedelta(hours=20), "read": False},
        {"id": 14, "title": "Hostel water outage notice", "placement": "alert", "result": "warning", "event": "emergency", "timestamp": now - datetime.timedelta(hours=7), "read": False},
        {"id": 15, "title": "Club meet tonight", "placement": "message", "result": "info", "event": "social", "timestamp": now - datetime.timedelta(hours=2, minutes=15), "read": False},
        {"id": 16, "title": "Semester registration open", "placement": "banner", "result": "success", "event": "deadline", "timestamp": now - datetime.timedelta(days=2), "read": False},
        {"id": 17, "title": "Guest Wi-Fi password changed", "placement": "summary", "result": "info", "event": "reminder", "timestamp": now - datetime.timedelta(minutes=30), "read": False},
        {"id": 18, "title": "Lab safety training due", "placement": "email", "result": "warning", "event": "deadline", "timestamp": now - datetime.timedelta(hours=16), "read": False},
        {"id": 19, "title": "Transit delay advisory", "placement": "message", "result": "warning", "event": "reminder", "timestamp": now - datetime.timedelta(hours=18), "read": False},
        {"id": 20, "title": "End-of-year cultural event details", "placement": "summary", "result": "info", "event": "social", "timestamp": now - datetime.timedelta(hours=9), "read": False},
    ]
    return sample_data


def _parse_timestamp(value):
    if isinstance(value, datetime.datetime):
        return value
    if isinstance(value, str):
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.datetime.strptime(value, fmt)
            except ValueError:
                continue
    return datetime.datetime.utcnow()


def fetch_notifications_from_api(url: str) -> List[dict]:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=10) as response:
        body = response.read().decode("utf-8")
        payload = json.loads(body)

    if isinstance(payload, dict) and "notifications" in payload:
        notifications = payload["notifications"]
    elif isinstance(payload, list):
        notifications = payload
    else:
        raise ValueError("Unexpected API payload format")

    parsed: List[dict] = []
    for notification in notifications:
        if not isinstance(notification, dict):
            continue
        notification = notification.copy()
        if "timestamp" in notification:
            notification["timestamp"] = _parse_timestamp(notification["timestamp"])
        else:
            notification["timestamp"] = datetime.datetime.utcnow()
        parsed.append(notification)

    return parsed


def render_screenshot(text: str, path: str = "priority_notifications_output.png") -> None:
    if Image is None or ImageDraw is None or ImageFont is None:
        return

    lines = text.splitlines()
    width = 900
    margin = 20
    line_height = 28
    height = margin * 2 + line_height * len(lines)

    image = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()

    y = margin
    for line in lines:
        draw.text((margin, y), line, fill=(30, 30, 30), font=font)
        y += line_height

    image.save(path)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Priority Inbox for unread notifications")
    parser.add_argument("--api-url", help="Notification API URL to fetch notifications from", default=None)
    parser.add_argument("--capacity", help="Number of top notifications to keep", type=int, default=10)
    args = parser.parse_args()

    inbox = PriorityInbox(capacity=args.capacity)

    if args.api_url:
        try:
            notifications = fetch_notifications_from_api(args.api_url)
        except (urllib.error.URLError, urllib.error.HTTPError, ValueError, json.JSONDecodeError) as error:
            print(f"Failed to fetch notifications from API: {error}")
            return
    else:
        notifications = build_sample_notifications()

    for notification in notifications:
        inbox.add_notification(notification)

    output = inbox.snapshot()
    print(output)

    if Image is not None:
        render_screenshot(output)
        print("Screenshot saved to priority_notifications_output.png")
    else:
        print("Pillow not installed; screenshot generation skipped.")

    with open("top_notifications.json", "w", encoding="utf-8") as file:
        json.dump(inbox.top_notifications(), file, default=str, indent=2)


if __name__ == "__main__":
    main()
