import asyncio
import logging
from datetime import UTC, datetime, timedelta

import musicbrainzngs

logger = logging.getLogger(__name__)


class MusicBrainzClient:
    """Client for interacting with the MusicBrainz API."""

    def __init__(self, app_name: str = "KeionBot", app_version: str = "0.1.0"):
        """Initialize the MusicBrainz client."""
        musicbrainzngs.set_useragent(app_name, app_version)

    async def get_daily_releases(self, days_ago: int = 1) -> list[dict]:
        """Fetch new releases from the last specified number of days."""
        loop = asyncio.get_event_loop()
        today = datetime.now(UTC).date()
        start_date = today - timedelta(days=days_ago)
        # Format dates for the query
        start_date_str = start_date.strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")

        # MusicBrainz search query for releases within a date range
        # Syntax: date:[START_DATE TO END_DATE]
        query = f"date:[{start_date_str} TO {today_str}]"
        logger.info(f"Querying MusicBrainz for releases with query: {query}")

        try:
            # musicbrainzngs is synchronous, run it in an executor
            result = await loop.run_in_executor(
                None,  # Use default executor
                lambda: musicbrainzngs.search_releases(query=query, limit=100),
            )
            releases = result.get("release-list", [])
            logger.info(
                f"Found {len(releases)} releases between "
                f"{start_date_str} and {today_str}"
            )
            return releases
        except musicbrainzngs.WebServiceError as e:
            logger.error(f"MusicBrainz API error: {e}")
            return []
        except Exception as e:
            logger.error(f"An unexpected error occurred fetching releases: {e}")
            return []
