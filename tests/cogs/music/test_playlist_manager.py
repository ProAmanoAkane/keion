import pytest

from keion.cogs.music.playlist_manager import PlaylistManager


@pytest.fixture
def playlist_manager():
    """Fixture for PlaylistManager."""
    return PlaylistManager()


def test_add_to_queue(playlist_manager: PlaylistManager):
    """Test adding a song to the queue."""
    song_info = {"title": "Test Song", "url": "http://example.com"}
    playlist_manager.add_to_queue(song_info)
    assert len(playlist_manager.playlist) == 1
    assert playlist_manager.playlist[0] == song_info


def test_clear_queue(playlist_manager: PlaylistManager):
    """Test clearing the queue."""
    song_info = {"title": "Test Song", "url": "http://example.com"}
    playlist_manager.add_to_queue(song_info)
    playlist_manager.current_song = song_info
    playlist_manager.clear_queue()
    assert len(playlist_manager.playlist) == 0
    assert playlist_manager.current_song is None


def test_get_next_song_empty(playlist_manager: PlaylistManager):
    """Test getting next song from an empty queue."""
    assert playlist_manager.get_next_song() is None
    assert playlist_manager.current_song is None


def test_get_next_song(playlist_manager: PlaylistManager):
    """Test getting the next song from the queue."""
    song1 = {"title": "Song 1", "url": "http://example.com/1"}
    song2 = {"title": "Song 2", "url": "http://example.com/2"}
    playlist_manager.add_to_queue(song1)
    playlist_manager.add_to_queue(song2)

    next_song = playlist_manager.get_next_song()
    assert next_song == song1
    assert playlist_manager.current_song == song1
    assert len(playlist_manager.playlist) == 1

    next_song = playlist_manager.get_next_song()
    assert next_song == song2
    assert playlist_manager.current_song == song2
    assert len(playlist_manager.playlist) == 0

    assert playlist_manager.get_next_song() is None


def test_skip_current_empty(playlist_manager: PlaylistManager):
    """Test skipping when queue is empty."""
    assert playlist_manager.skip_current() is None


def test_skip_current_with_queue(playlist_manager: PlaylistManager):
    """Test skipping the current song when others are in queue."""
    song1 = {"title": "Song 1", "url": "http://example.com/1"}
    song2 = {"title": "Song 2", "url": "http://example.com/2"}
    playlist_manager.add_to_queue(song1)
    playlist_manager.add_to_queue(song2)
    playlist_manager.current_song = playlist_manager.get_next_song()  # song1 is current

    skipped_to = playlist_manager.skip_current()
    assert skipped_to == song2
    assert playlist_manager.current_song == song2
    assert len(playlist_manager.playlist) == 0


def test_toggle_loop_queue(playlist_manager: PlaylistManager):
    """Test toggling queue loop."""
    assert not playlist_manager.loop_queue
    playlist_manager.toggle_loop_queue()
    assert playlist_manager.loop_queue
    assert not playlist_manager.loop_song
    playlist_manager.toggle_loop_queue()
    assert not playlist_manager.loop_queue


def test_toggle_loop_song(playlist_manager: PlaylistManager):
    """Test toggling song loop."""
    assert not playlist_manager.loop_song
    playlist_manager.toggle_loop_song()
    assert playlist_manager.loop_song
    assert not playlist_manager.loop_queue
    playlist_manager.toggle_loop_song()
    assert not playlist_manager.loop_song


def test_song_finished_no_loop(playlist_manager: PlaylistManager):
    """Test song finished logic without looping."""
    song1 = {"title": "Song 1", "url": "http://example.com/1"}
    playlist_manager.add_to_queue(song1)
    playlist_manager.current_song = playlist_manager.get_next_song()  # song1 is current

    next_song = playlist_manager.song_finished()
    assert next_song is None  # Queue is now empty
    assert playlist_manager.current_song is None


def test_song_finished_loop_song(playlist_manager: PlaylistManager):
    """Test song finished logic with song loop enabled."""
    song1 = {"title": "Song 1", "url": "http://example.com/1"}
    playlist_manager.add_to_queue(song1)
    playlist_manager.current_song = playlist_manager.get_next_song()  # song1 is current
    playlist_manager.toggle_loop_song()

    next_song = playlist_manager.song_finished()
    assert next_song == song1  # Should replay song1
    assert playlist_manager.current_song == song1  # Current song remains song1


def test_song_finished_loop_queue(playlist_manager: PlaylistManager):
    """Test song finished logic with queue loop enabled."""
    song1 = {"title": "Song 1", "url": "http://example.com/1"}
    song2 = {"title": "Song 2", "url": "http://example.com/2"}
    playlist_manager.add_to_queue(song1)
    playlist_manager.add_to_queue(song2)
    playlist_manager.toggle_loop_queue()  # Enable loop, backup created [song1, song2]

    playlist_manager.current_song = (
        playlist_manager.get_next_song()
    )  # song1 is current, queue=[song2], backup=[song1, song2]
    next_song = playlist_manager.song_finished()  # song1 finishes naturally
    assert next_song == song2  # Next is song2
    assert playlist_manager.current_song == song2  # Current is song2

    playlist_manager.current_song = (
        playlist_manager.get_next_song()
    )  # song2 is current, queue=[], backup=[song1, song2]
    next_song = playlist_manager.song_finished()  # song2 finishes naturally
    assert next_song == song1  # Queue restored from backup, next is song1
    assert playlist_manager.current_song == song1  # Current is song1
    assert len(playlist_manager.playlist) == 1  # playlist is now [song2]
