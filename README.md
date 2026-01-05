# User Events Merger

Implementation of `merge_user_events()` function that groups user events into sessions.

## Requirements

- Python 3.8+

## Installation

```bash
pip install -r requirements.txt
```

## Usage

```python
from merge_events import merge_user_events

events = [
    {"user_id": "u1", "ts": 1700000000, "type": "click", "meta": {"page": "/"}},
    {"user_id": "u1", "ts": 1700000600, "type": "view", "meta": {"page": "/about"}},
]

sessions = merge_user_events(events)
```

## Testing

```bash
pytest test_merge_events.py -v
```

## Implementation Details

- Sessions are created when events for the same user are <= 600 seconds apart
- Types array preserves chronological order and counts
- Meta objects are deep merged (recursive, earliest value on conflict)
- Output sorted by start_ts ascending

