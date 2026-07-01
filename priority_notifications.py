import argparse
import datetime
import heapq
import json
import urllib.request


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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--api-url",
        default="http://4.224.186.213/evaluation-service/notifications",
        help="Notification API URL (default uses the provided endpoint)",
    )
    parser.add_argument("--n", type=int, default=10, help="Number of top notifications")
    parser.add_argument("--limit", type=int, default=10, help="API limit query parameter")
    parser.add_argument("--page", type=int, default=1, help="API page query parameter")
    parser.add_argument("--notification-type", default=None, help="API notification_type query parameter")
    args = parser.parse_args()
    try:
        notifications = fetch(
            args.api_url,
            limit=args.limit,
            page=args.page,
            notification_type=args.notification_type,
        )
    except Exception as e:
        print("Fetch error:", e)
        return
    for idx, item in enumerate(top_n(notifications, args.n), start=1):
        print(f"{idx}. {item.get('title','<no title>')} ({item.get('placement')},{item.get('result')},{item.get('event')})")


if __name__ == "__main__":
    main()
