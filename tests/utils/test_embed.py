"""Tests for the EmbedBuilder."""

from keion.utils.embed import EmbedBuilder


# TODO: Add more comprehensive tests for different song_info structures
def test_now_playing_basic():
    """Test basic now_playing embed creation."""
    builder = EmbedBuilder()
    song_info = {
        "title": "Test Song",
        "webpage_url": "http://example.com",
        "artist": "Test Artist",
        "duration": 185,  # 3:05
        "thumbnail": "http://example.com/thumb.jpg",
    }
    embed = builder.now_playing(song_info)
    assert embed.title == "Test Song"
    assert "Test Artist" in embed.fields[0].value
    assert "03:05" in embed.fields[0].value
    assert embed.thumbnail.url == "http://example.com/thumb.jpg"


def test_format_duration():
    """Test duration formatting."""
    assert EmbedBuilder._format_duration(185) == "03:05"
    assert EmbedBuilder._format_duration(59) == "00:59"
    assert EmbedBuilder._format_duration(3600) == "60:00"  # Or handle hours if needed
    assert EmbedBuilder._format_duration(0) == "00:00"
    assert EmbedBuilder._format_duration(None) == "??:??"
