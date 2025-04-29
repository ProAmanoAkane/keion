"""Tests for web utility functions."""

from datetime import UTC, datetime, timedelta

import pytest

from keion.web.utils import format_uptime  # , get_stats, get_players

# TODO: Add tests for get_stats and get_players (requires mocking bot/cogs)


@pytest.mark.parametrize(
    "start_time, expected",
    [
        (datetime.now(UTC) - timedelta(minutes=5, seconds=30), "5m"),
        (datetime.now(UTC) - timedelta(hours=2, minutes=15), "2h 15m"),
        (datetime.now(UTC) - timedelta(days=3, hours=1), "3d 1h"),
        (datetime.now(UTC) - timedelta(seconds=45), "45s"),
        (datetime.now(UTC) - timedelta(minutes=0), "0s"),  # Test exactly now
        (datetime.now(UTC), "0s"),  # Test exactly now (alternative)
        (None, "N/A"),
    ],
)
def test_format_uptime(start_time, expected):
    """Test uptime formatting."""
    assert format_uptime(start_time) == expected
