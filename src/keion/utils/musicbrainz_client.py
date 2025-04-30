import asyncio
import logging
from datetime import UTC, datetime, timedelta

import aiohttp
import musicbrainzngs

logger = logging.getLogger(__name__)


class MusicBrainzClient:
    """Client for interacting with the MusicBrainz API."""

    def __init__(self, app_name: str = "KeionBot", app_version: str = "0.1.0"):
        """Initialize the MusicBrainz client."""
        musicbrainzngs.set_useragent(app_name, app_version)
        self._session = None  # aiohttp session will be created on demand

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp ClientSession."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close_session(self) -> None:
        """Close the aiohttp ClientSession."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def get_daily_releases(self, days_ago: int = 1) -> list[dict]:
        """Fetch new releases from the last specified number of days."""
        loop = asyncio.get_event_loop()
        today = datetime.now(UTC).date()
        start_date = today - timedelta(days=days_ago)
        query_date = start_date.strftime("%Y-%m-%d")

        # MusicBrainz search query for releases on a specific date
        # Note: MusicBrainz date queries can be complex. This searches for releases
        # with the *exact* date specified.
        # Fetching a range might require multiple queries
        # or a different approach depending on exact needs.
        query = f"date:{query_date}"
        logger.info(f"Querying MusicBrainz for releases with query: {query}")

        try:
            # musicbrainzngs is synchronous, run it in an executor
            result = await loop.run_in_executor(
                None,  # Use default executor
                lambda: musicbrainzngs.search_releases(query=query, limit=100),
            )
            releases = result.get("release-list", [])
            logger.info(f"Found {len(releases)} releases for date {query_date}")
            return releases
        except musicbrainzngs.WebServiceError as e:
            logger.error(f"MusicBrainz API error: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred fetching releases: {e}")
            return []

    async def __aenter__(self):
        await self._get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()
