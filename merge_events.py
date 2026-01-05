"""
User Events Merger

Groups user events into sessions based on time gaps.
"""

from typing import Dict, List, Any


def merge_user_events(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge user events into sessions.
    
    A session is a consecutive run of events for the same user_id where
    adjacent events are at most 10 minutes apart (<= 600 seconds).
    
    Args:
        events: List of event dictionaries, each containing:
            - user_id: str
            - ts: int (timestamp)
            - type: str (event type)
            - meta: dict (optional metadata)
    
    Returns:
        List of session dictionaries, each containing:
            - user_id: str
            - start_ts: int (earliest timestamp in session)
            - end_ts: int (latest timestamp in session)
            - types: List[str] (chronological unique types with counts preserved)
            - meta: dict (deep merged metadata)
        
        Sorted by start_ts ascending.
    
    Example:
        >>> events = [
        ...     {"user_id": "u1", "ts": 1000, "type": "click", "meta": {"page": "/"}},
        ...     {"user_id": "u1", "ts": 1500, "type": "view", "meta": {"page": "/about"}},
        ... ]
        >>> sessions = merge_user_events(events)
        >>> len(sessions)
        1
        >>> sessions[0]["start_ts"]
        1000
    """
    if not events:
        return []
    
    # Sort events by user_id and timestamp to group properly
    sorted_events = sorted(events, key=lambda e: (e["user_id"], e["ts"]))
    
    # Group events by user_id
    user_events: Dict[str, List[Dict[str, Any]]] = {}
    for event in sorted_events:
        user_id = event["user_id"]
        if user_id not in user_events:
            user_events[user_id] = []
        user_events[user_id].append(event)
    
    # Create sessions for each user
    all_sessions: List[Dict[str, Any]] = []
    
    for user_id, user_event_list in user_events.items():
        sessions = _create_sessions_for_user(user_id, user_event_list)
        all_sessions.extend(sessions)
    
    # Sort all sessions by start_ts ascending
    return sorted(all_sessions, key=lambda s: s["start_ts"])


def _create_sessions_for_user(user_id: str, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Create sessions for a single user's events.
    
    Sessions are split when gap between consecutive events > 600 seconds.
    """
    if not events:
        return []
    
    sessions: List[Dict[str, Any]] = []
    current_session: List[Dict[str, Any]] = [events[0]]
    
    for i in range(1, len(events)):
        prev_ts = events[i - 1]["ts"]
        curr_ts = events[i]["ts"]
        gap = curr_ts - prev_ts
        
        if gap <= 600:
            # Same session
            current_session.append(events[i])
        else:
            # New session - finalize current and start new
            sessions.append(_build_session(user_id, current_session))
            current_session = [events[i]]
    
    # Don't forget the last session
    if current_session:
        sessions.append(_build_session(user_id, current_session))
    
    return sessions


def _build_session(user_id: str, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Build a session dictionary from a list of events.
    
    - start_ts: minimum timestamp
    - end_ts: maximum timestamp
    - types: chronological unique types with counts preserved
    - meta: deep merged metadata
    """
    timestamps = [e["ts"] for e in events]
    start_ts = min(timestamps)
    end_ts = max(timestamps)
    
    # Types: chronological order, duplicates removed but counts preserved
    # Track unique types in order of first occurrence
    type_order: List[str] = []
    type_seen: set = set()
    
    for event in events:
        event_type = event["type"]
        if event_type not in type_seen:
            type_order.append(event_type)
            type_seen.add(event_type)
    
    # Return unique types in chronological order of first occurrence
    types = type_order
    
    # Deep merge meta objects
    meta = {}
    for event in events:
        event_meta = event.get("meta", {})
        if event_meta:
            meta = _deep_merge_meta(meta, event_meta)
    
    return {
        "user_id": user_id,
        "start_ts": start_ts,
        "end_ts": end_ts,
        "types": types,
        "meta": meta,
    }


def _deep_merge_meta(base: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deep merge two meta dictionaries.
    
    Rules:
    - If both have a key with dict values, merge recursively
    - If there's a conflict on a non-dict value, keep the earliest value (base)
      Since events are processed in chronological order, base always comes first.
    """
    result = base.copy()
    
    for key, new_value in new.items():
        if key not in result:
            # New key, just add it
            result[key] = new_value
        else:
            base_value = result[key]
            # Both have the key
            if isinstance(base_value, dict) and isinstance(new_value, dict):
                # Both are dicts, merge recursively
                result[key] = _deep_merge_meta(base_value, new_value)
            else:
                # Conflict on non-dict value, keep the earliest (base comes first)
                result[key] = base_value
    
    return result

