# Campus Evaluation Notification System 

A priority-based notification inbox system that dynamically ranks campus notifications by importance and recency. This project implements an efficient ranking algorithm using a Min-Heap (`O(log n)` insertion complexity) to maintain the top `N` most relevant notifications for users.

---

## 🚀 Key Features

*   **Min-Heap Dynamic Ranking**: Instead of sorting the entire database of notifications (which is inefficient for large volumes), the system processes notifications in a streaming fashion using a min-heap to keep track of the top `N` notifications.
*   **Weighted Scoring Algorithm**: Computes relevance scores based on:
    *   **Placement Type** (e.g., banner, alert, email, message, summary)
    *   **Result Urgency** (e.g., success, warning, info, fail)
    *   **Event Relevance** (e.g., deadline, emergency, meeting, reminder, social)
    *   **Recency Decay** (favors newer notifications while smoothly decaying the score of older ones over time)
*   **Lightweight Script**: `priority_inbox_simple.py` fetches unread notifications directly from the campus endpoint, ranks them, and outputs the top `N`.
*   **JSON Serialization**: Outputs the final top notifications into `top_notifications.json`.

---

## 📐 Scoring Formula

The relevance score of each notification is calculated using the following formula:

$$\text{Score} = (\text{Placement Weight} \times 0.35) + (\text{Result Weight} \times 0.25) + (\text{Event Weight} \times 0.25) + (\text{Recency Score} \times 1.5)$$

Where:
*   **Recency Score**: Defined as $1 / (1 + \text{age in hours})$, decaying smoothly over time.
*   **Placement Weights**: `banner` (5.0), `alert` (4.0), `email` (3.0), `message` (2.0), `summary` (1.0)
*   **Result Weights**: `success` (4.0), `warning` (3.0), `info` (2.0), `fail` (1.0)
*   **Event Weights**: `deadline` (5.0), `emergency` (4.0), `meeting` (3.0), `reminder` (2.0), `social` (1.0)

---

## 🛠️ Project Structure

```
.
├── Notification_System_Design.md   # Architectural overview and design principles
├── priority_inbox_simple.py       # Simple lightweight API client and ranking implementation
└── README.md                       # Project documentation (this file)
```

---

## 🏃 Getting Started

### 1. Installation

This project is built using Python 3 and has no external dependencies.

### 2. Running the Inbox ranking

To run the lightweight direct API script:

```bash
python priority_inbox_simple.py
```

---

## 📄 Outputs

Once run, the script generates:
*   `top_notifications.json`: A JSON list containing the top ranked notifications.
