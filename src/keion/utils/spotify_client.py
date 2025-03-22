"""Spotify API client implementation."""

import os
import requests
from typing import Dict, Any, Tuple
from urllib.parse import urlencode


class SpotifyAPIError(Exception):
    """Custom exception for Spotify API errors."""

    pass


class SpotifyClient:
    """Client for interacting with Spotify Web API."""

    def __init__(self):
        """Initialize Spotify client with credentials from environment."""
        self.client_id = os.getenv("SPOTIFY_CLIENT_ID")
        self.client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

        if not all([self.client_id, self.client_secret]):
            raise ValueError("Spotify credentials not found in environment")

        self._secrets: Tuple[str, str] = (self.client_id, self.client_secret)
        self._session = requests.Session()

        # Set up session with initial headers
        self._session.headers.update(
            {"Content-Type": "application/x-www-form-urlencoded"}
        )
        self._session.params.update({"market": "US"})

        # Get initial token and update headers
        self._session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._get_token()}",
            }
        )

    def _get_token(self) -> str:
        """Obtain access token using client credentials flow."""
        token_endpoint = "https://accounts.spotify.com/api/token"
        response = self._session.post(
            token_endpoint,
            data={"grant_type": "client_credentials"},
            auth=self._secrets,
        )

        if response.status_code != 200:
            raise SpotifyAPIError("Failed to authenticate with Spotify")

        return response.json()["access_token"]

    def _refresh_token_if_needed(self, response: requests.Response) -> bool:
        """Refresh token if expired and update session headers."""
        if response.status_code == 401:
            token = self._get_token()
            self._session.headers.update({"Authorization": f"Bearer {token}"})
            return True
        return False

    def get_track_info(self, track_id: str) -> Dict[str, Any]:
        """Get track information from Spotify API."""
        response = self._session.get(f"https://api.spotify.com/v1/tracks/{track_id}")

        if self._refresh_token_if_needed(response):
            return self.get_track_info(track_id)

        if response.status_code != 200:
            raise SpotifyAPIError(
                f"Failed to fetch track information: {response.status_code}"
            )

        return response.json()

    def search_track(self, query: str) -> Dict[str, Any]:
        """Search for a track on Spotify."""
        params = urlencode({"q": query, "type": "track", "limit": 1})
        response = self._session.get(f"https://api.spotify.com/v1/search?{params}")

        if self._refresh_token_if_needed(response):
            return self.search_track(query)

        if response.status_code != 200:
            raise SpotifyAPIError(f"Failed to search for track: {response.status_code}")

        return response.json()
