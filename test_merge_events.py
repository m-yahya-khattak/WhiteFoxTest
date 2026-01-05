"""
Test suite for merge_user_events function.
"""

import pytest
from merge_events import merge_user_events


def test_empty_events():
    """Test with empty events list."""
    assert merge_user_events([]) == []


def test_single_event():
    """Test with a single event."""
    events = [
        {"user_id": "u1", "ts": 1000, "type": "click", "meta": {"page": "/"}},
    ]
    result = merge_user_events(events)
    assert len(result) == 1
    assert result[0]["user_id"] == "u1"
    assert result[0]["start_ts"] == 1000
    assert result[0]["end_ts"] == 1000
    assert result[0]["types"] == ["click"]
    assert result[0]["meta"] == {"page": "/"}


def test_same_session_under_600s():
    """Test events within 600s gap are in same session."""
    events = [
        {"user_id": "u1", "ts": 1000, "type": "click", "meta": {"page": "/"}},
        {"user_id": "u1", "ts": 1500, "type": "view", "meta": {"page": "/about"}},
    ]
    result = merge_user_events(events)
    assert len(result) == 1
    assert result[0]["start_ts"] == 1000
    assert result[0]["end_ts"] == 1500
    assert result[0]["types"] == ["click", "view"]


def test_exactly_600s_gap():
    """Test events exactly 600s apart are in same session."""
    events = [
        {"user_id": "u1", "ts": 1000, "type": "click", "meta": {}},
        {"user_id": "u1", "ts": 1600, "type": "view", "meta": {}},
    ]
    result = merge_user_events(events)
    assert len(result) == 1


def test_over_600s_gap_new_session():
    """Test events over 600s apart create new session."""
    events = [
        {"user_id": "u1", "ts": 1000, "type": "click", "meta": {}},
        {"user_id": "u1", "ts": 1500, "type": "view", "meta": {}},
        {"user_id": "u1", "ts": 2200, "type": "click", "meta": {}},  # 700s gap
    ]
    result = merge_user_events(events)
    assert len(result) == 2
    assert result[0]["start_ts"] == 1000
    assert result[0]["end_ts"] == 1500
    assert result[1]["start_ts"] == 2200
    assert result[1]["end_ts"] == 2200


def test_multiple_users():
    """Test events from multiple users."""
    events = [
        {"user_id": "u2", "ts": 2000, "type": "click", "meta": {}},
        {"user_id": "u1", "ts": 1000, "type": "view", "meta": {}},
        {"user_id": "u1", "ts": 1500, "type": "click", "meta": {}},
    ]
    result = merge_user_events(events)
    assert len(result) == 2
    # Should be sorted by start_ts
    assert result[0]["user_id"] == "u1"
    assert result[0]["start_ts"] == 1000
    assert result[1]["user_id"] == "u2"
    assert result[1]["start_ts"] == 2000


def test_unsorted_input():
    """Test that unsorted input is handled correctly."""
    events = [
        {"user_id": "u1", "ts": 1500, "type": "view", "meta": {}},
        {"user_id": "u1", "ts": 1000, "type": "click", "meta": {}},
        {"user_id": "u1", "ts": 1200, "type": "scroll", "meta": {}},
    ]
    result = merge_user_events(events)
    assert len(result) == 1
    assert result[0]["start_ts"] == 1000
    assert result[0]["end_ts"] == 1500
    # Types should be in chronological order
    assert result[0]["types"] == ["click", "scroll", "view"]


def test_types_duplicates_removed():
    """Test that duplicate types are removed but order preserved."""
    events = [
        {"user_id": "u1", "ts": 1000, "type": "click", "meta": {}},
        {"user_id": "u1", "ts": 1100, "type": "view", "meta": {}},
        {"user_id": "u1", "ts": 1200, "type": "click", "meta": {}},  # Duplicate
        {"user_id": "u1", "ts": 1300, "type": "scroll", "meta": {}},
    ]
    result = merge_user_events(events)
    assert len(result) == 1
    # Types should be unique but in chronological order of first occurrence
    assert result[0]["types"] == ["click", "view", "scroll"]


def test_meta_simple_merge():
    """Test simple meta merge."""
    events = [
        {"user_id": "u1", "ts": 1000, "type": "click", "meta": {"page": "/"}},
        {"user_id": "u1", "ts": 1100, "type": "view", "meta": {"section": "header"}},
    ]
    result = merge_user_events(events)
    assert len(result) == 1
    assert result[0]["meta"] == {"page": "/", "section": "header"}


def test_meta_deep_merge():
    """Test recursive meta merge."""
    events = [
        {"user_id": "u1", "ts": 1000, "type": "click", "meta": {"user": {"name": "Alice"}}},
        {"user_id": "u1", "ts": 1100, "type": "view", "meta": {"user": {"age": 30}}},
    ]
    result = merge_user_events(events)
    assert len(result) == 1
    assert result[0]["meta"] == {"user": {"name": "Alice", "age": 30}}


def test_meta_conflict_earliest_wins():
    """Test that on meta conflict, earliest value wins."""
    events = [
        {"user_id": "u1", "ts": 1000, "type": "click", "meta": {"page": "/home"}},
        {"user_id": "u1", "ts": 1100, "type": "view", "meta": {"page": "/about"}},
    ]
    result = merge_user_events(events)
    assert len(result) == 1
    # Earliest value should win
    assert result[0]["meta"]["page"] == "/home"


def test_meta_missing():
    """Test events with missing meta field."""
    events = [
        {"user_id": "u1", "ts": 1000, "type": "click"},
        {"user_id": "u1", "ts": 1100, "type": "view", "meta": {"page": "/"}},
    ]
    result = merge_user_events(events)
    assert len(result) == 1
    assert result[0]["meta"] == {"page": "/"}


def test_meta_empty_dict():
    """Test events with empty meta dict."""
    events = [
        {"user_id": "u1", "ts": 1000, "type": "click", "meta": {}},
        {"user_id": "u1", "ts": 1100, "type": "view", "meta": {"page": "/"}},
    ]
    result = merge_user_events(events)
    assert len(result) == 1
    assert result[0]["meta"] == {"page": "/"}


def test_complex_scenario():
    """Test a complex scenario with multiple users and sessions."""
    events = [
        {"user_id": "u1", "ts": 1000, "type": "click", "meta": {"page": "/"}},
        {"user_id": "u1", "ts": 1500, "type": "view", "meta": {"page": "/about"}},
        {"user_id": "u1", "ts": 2200, "type": "click", "meta": {"page": "/contact"}},  # New session
        {"user_id": "u2", "ts": 500, "type": "view", "meta": {"page": "/"}},
        {"user_id": "u2", "ts": 800, "type": "click", "meta": {"page": "/products"}},
    ]
    result = merge_user_events(events)
    assert len(result) == 3
    # Should be sorted by start_ts
    assert result[0]["user_id"] == "u2"
    assert result[0]["start_ts"] == 500
    assert result[1]["user_id"] == "u1"
    assert result[1]["start_ts"] == 1000
    assert result[2]["user_id"] == "u1"
    assert result[2]["start_ts"] == 2200


def test_input_not_modified():
    """Test that input events are not modified in-place."""
    events = [
        {"user_id": "u1", "ts": 1000, "type": "click", "meta": {"page": "/"}},
    ]
    original_events = [e.copy() for e in events]
    merge_user_events(events)
    assert events == original_events

