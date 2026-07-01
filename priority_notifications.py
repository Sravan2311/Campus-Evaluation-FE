import argparse
import datetime
import heapq
import json
import urllib.request
import urllib.parse
import os

# Try to import PIL for generating visualization
try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

def parse_ts(v):
    if isinstance(v, datetime.datetime):
        return v
    for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.datetime.strptime(v, fmt)
        except Exception:
            pass
    return datetime.datetime.utcnow()

def score(n, now=None):
    now = now or datetime.datetime.utcnow()
    p = {"banner": 5, "alert": 4, "email": 3, "message": 2, "summary": 1}.get(n.get("placement"), 1)
    r = {"success": 4, "warning": 3, "info": 2, "fail": 1}.get(n.get("result"), 2)
    e = {"deadline": 5, "emergency": 4, "meeting": 3, "reminder": 2, "social": 1}.get(n.get("event"), 1)
    t = parse_ts(n.get("timestamp", ""))
    age = max((now - t).total_seconds() / 3600, 0)
    return p * 0.35 + r * 0.25 + e * 0.25 + 1.5 / (1 + age)

def get_mock_notifications():
    # Return a rich dataset of 25 mock notifications for demonstration/fallback
    base_time = datetime.datetime.utcnow()
    return [
        {
            "id": "mock-1",
            "title": "EMERGENCY: Fire Drill in Block A",
            "placement": "alert",
            "result": "warning",
            "event": "emergency",
            "timestamp": (base_time - datetime.timedelta(minutes=5)).isoformat() + "Z",
            "read": False,
            "notification_type": "Event"
        },
        {
            "id": "mock-2",
            "title": "CRITICAL: Final Semester Registration Deadline",
            "placement": "banner",
            "result": "fail",
            "event": "deadline",
            "timestamp": (base_time - datetime.timedelta(minutes=15)).isoformat() + "Z",
            "read": False,
            "notification_type": "Event"
        },
        {
            "id": "mock-3",
            "title": "Placement Cell: Interview scheduled with Google",
            "placement": "email",
            "result": "success",
            "event": "meeting",
            "timestamp": (base_time - datetime.timedelta(hours=1)).isoformat() + "Z",
            "read": False,
            "notification_type": "Placement"
        },
        {
            "id": "mock-4",
            "title": "System Update: Campus Wi-Fi maintenance tonight",
            "placement": "summary",
            "result": "info",
            "event": "reminder",
            "timestamp": (base_time - datetime.timedelta(hours=3)).isoformat() + "Z",
            "read": False,
            "notification_type": "Result"
        },
        {
            "id": "mock-5",
            "title": "Urgent Message from HOD: Seminar attendance required",
            "placement": "message",
            "result": "warning",
            "event": "emergency",
            "timestamp": (base_time - datetime.timedelta(hours=2)).isoformat() + "Z",
            "read": False,
            "notification_type": "Event"
        },
        {
            "id": "mock-6",
            "title": "Library Book Due Date Tomorrow",
            "placement": "message",
            "result": "info",
            "event": "reminder",
            "timestamp": (base_time - datetime.timedelta(hours=6)).isoformat() + "Z",
            "read": False,
            "notification_type": "Event"
        },
        {
            "id": "mock-7",
            "title": "Sports Club: Annual Meet registrations open",
            "placement": "summary",
            "result": "success",
            "event": "social",
            "timestamp": (base_time - datetime.timedelta(hours=12)).isoformat() + "Z",
            "read": False,
            "notification_type": "Placement"
        },
        {
            "id": "mock-8",
            "title": "Midterm Results Published - Check Portal",
            "placement": "banner",
            "result": "success",
            "event": "reminder",
            "timestamp": (base_time - datetime.timedelta(hours=8)).isoformat() + "Z",
            "read": False,
            "notification_type": "Result"
        },
        {
            "id": "mock-9",
            "title": "Canteen: Special lunch menu today",
            "placement": "summary",
            "result": "info",
            "event": "social",
            "timestamp": (base_time - datetime.timedelta(minutes=45)).isoformat() + "Z",
            "read": False,
            "notification_type": "Event"
        },
        {
            "id": "mock-10",
            "title": "Payment Gateway Error: Hostel fee receipt failed",
            "placement": "alert",
            "result": "fail",
            "event": "deadline",
            "timestamp": (base_time - datetime.timedelta(hours=4)).isoformat() + "Z",
            "read": False,
            "notification_type": "Result"
        },
        {
            "id": "mock-11",
            "title": "Club Meet: Coding Club Hackathon brainstorming",
            "placement": "message",
            "result": "info",
            "event": "meeting",
            "timestamp": (base_time - datetime.timedelta(hours=10)).isoformat() + "Z",
            "read": False,
            "notification_type": "Event"
        },
        {
            "id": "mock-12",
            "title": "New Assignment uploaded in DBMS course",
            "placement": "email",
            "result": "info",
            "event": "reminder",
            "timestamp": (base_time - datetime.timedelta(hours=24)).isoformat() + "Z",
            "read": False,
            "notification_type": "Event"
        }
    ]

def fetch(url, limit=None, page=None, notification_type=None):
    query = {}
    if limit is not None:
        query["limit"] = str(limit)
    if page is not None:
        query["page"] = str(page)
    if notification_type:
        query["notification_type"] = notification_type
    parsed = list(urllib.parse.urlparse(url))
    parsed[4] = urllib.parse.urlencode(query)
    url_with_query = urllib.parse.urlunparse(parsed)

    # Note: If unauthorized, we catch it and raise, falling back to mock data
    req = urllib.request.Request(url_with_query, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode())
    if isinstance(data, dict) and "notifications" in data:
        data = data["notifications"]
    return [dict(n, timestamp=parse_ts(n.get("timestamp", ""))) for n in data if isinstance(n, dict)]

def top_n(items, n=10):
    heap = []
    for item in items:
        if item.get("read"):
            continue
        s = score(item)
        if len(heap) < n:
            heapq.heappush(heap, (s, item))
        elif s > heap[0][0]:
            heapq.heapreplace(heap, (s, item))
    return [item for _, item in sorted(heap, key=lambda x: x[0], reverse=True)]

def draw_notifications_image(items, output_path):
    if not HAS_PIL:
        print("PIL/Pillow is not installed. Skipping image generation.")
        return False
    
    width = 900
    header_height = 80
    card_height = 100
    spacing = 15
    height = header_height + len(items) * (card_height + spacing) + 40
    
    # Create image
    img = Image.new("RGB", (width, height), color="#0f172a") # Dark Slate background
    draw = ImageDraw.Draw(img)
    
    # Load fonts
    try:
        title_font = ImageFont.truetype("arial.ttf", 26)
        subtitle_font = ImageFont.truetype("arial.ttf", 14)
        card_title_font = ImageFont.truetype("arial.ttf", 16)
        card_text_font = ImageFont.truetype("arial.ttf", 12)
        score_font = ImageFont.truetype("arial.ttf", 18)
    except IOError:
        # Fallback to default font
        title_font = subtitle_font = card_title_font = card_text_font = score_font = ImageFont.load_default()
        
    # Draw Header
    draw.text((30, 20), "Priority Notifications Inbox", fill="#f8fafc", font=title_font)
    draw.text((30, 52), f"Top {len(items)} Unread Notifications - Ranked by Recency and Severity Score", fill="#94a3b8", font=subtitle_font)
    
    # Draw divider line
    draw.line((30, 75, width - 30, 75), fill="#334155", width=2)
    
    y_offset = header_height + 20
    
    # Draw cards
    for idx, item in enumerate(items, start=1):
        s = score(item)
        
        # Color mapping based on event/result
        badge_color = "#3b82f6" # Default blue
        event = item.get("event", "")
        result = item.get("result", "")
        
        if event == "emergency" or event == "deadline":
            badge_color = "#ef4444" # Red
        elif result == "warning":
            badge_color = "#f59e0b" # Amber
        elif result == "success":
            badge_color = "#10b981" # Emerald
        elif event == "social":
            badge_color = "#8b5cf6" # Violet
            
        # Draw Card Background
        card_left = 30
        card_top = y_offset
        card_right = width - 30
        card_bottom = y_offset + card_height
        
        # Draw card rounded rect
        draw.rounded_rectangle((card_left, card_top, card_right, card_bottom), radius=8, fill="#1e293b", outline="#334155", width=1)
        
        # Draw Left Severity Stripe
        draw.rounded_rectangle((card_left, card_top, card_left + 8, card_bottom), radius=8, fill=badge_color)
        # Rect cover to make the right edge of stripe flat
        draw.rectangle((card_left + 4, card_top, card_left + 8, card_bottom), fill=badge_color)
        
        # Text details
        title = f"{idx}. {item.get('title', '<No Title>')}"
        if len(title) > 60:
            title = title[:57] + "..."
            
        time_str = parse_ts(item.get("timestamp")).strftime("%Y-%m-%d %H:%M:%S UTC")
        meta_str = f"Placement: {item.get('placement')}   |   Event: {item.get('event')}   |   Result: {item.get('result')}"
        
        draw.text((card_left + 25, card_top + 15), title, fill="#f8fafc", font=card_title_font)
        draw.text((card_left + 25, card_top + 45), meta_str, fill="#94a3b8", font=card_text_font)
        draw.text((card_left + 25, card_top + 68), f"Time: {time_str}", fill="#64748b", font=card_text_font)
        
        # Draw score circle/badge on the right
        score_bg_left = card_right - 120
        score_bg_top = card_top + 25
        score_bg_right = card_right - 25
        score_bg_bottom = card_bottom - 25
        
        draw.rounded_rectangle((score_bg_left, score_bg_top, score_bg_right, score_bg_bottom), radius=6, fill="#0f172a", outline="#334155", width=1)
        score_txt = f"Score: {s:.2f}"
        
        # Draw score text centered in badge
        draw.text((score_bg_left + 12, score_bg_top + 13), score_txt, fill="#38bdf8", font=score_font)
        
        y_offset += card_height + spacing
        
    # Save Image
    img.save(output_path)
    print(f"Generated priority visualization image at {output_path}")
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api-url",
        default="http://4.224.186.213/evaluation-service/notifications",
        help="Notification API URL (default uses the provided endpoint)",
    )
    parser.add_argument("--n", type=int, default=10, help="Number of top notifications")
    parser.add_argument("--limit", type=int, default=50, help="API limit query parameter")
    parser.add_argument("--page", type=int, default=1, help="API page query parameter")
    parser.add_argument("--notification-type", default=None, help="API notification_type query parameter")
    args = parser.parse_args()
    
    notifications = []
    fetched_successfully = False
    
    try:
        print(f"Fetching notifications from {args.api_url}...")
        notifications = fetch(
            args.api_url,
            limit=args.limit,
            page=args.page,
            notification_type=args.notification_type,
        )
        fetched_successfully = True
        print(f"Successfully fetched {len(notifications)} notifications from the API.")
    except Exception as e:
        print(f"Fetch error: {e}")
        print("Falling back to mock campus notification dataset...")
        notifications = get_mock_notifications()
        # Parse timestamps in mock data
        for n in notifications:
            n["timestamp"] = parse_ts(n.get("timestamp"))
            
    # Calculate top notifications
    top_list = top_n(notifications, args.n)
    
    # Print to console
    print("\n================ TOP NOTIFICATIONS ================")
    for idx, item in enumerate(top_list, start=1):
        s = score(item)
        print(f"{idx}. {item.get('title','<no title>')} [Score: {s:.2f}] ({item.get('placement')},{item.get('result')},{item.get('event')})")
    print("===================================================\n")
    
    # Write top_notifications.json
    # Convert timestamps back to ISO strings for JSON serialization
    json_list = []
    for item in top_list:
        n_copy = item.copy()
        if isinstance(n_copy["timestamp"], datetime.datetime):
            n_copy["timestamp"] = n_copy["timestamp"].isoformat() + "Z"
        n_copy["score"] = score(item)
        json_list.append(n_copy)
        
    json_path = "top_notifications.json"
    with open(json_path, "w") as f:
        json.dump(json_list, f, indent=2)
    print(f"Saved ranked notifications to {json_path}")
    
    # Generate visualization
    image_path = "priority_notifications_output.png"
    draw_notifications_image(top_list, image_path)

if __name__ == "__main__":
    main()
