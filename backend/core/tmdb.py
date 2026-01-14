from __future__ import annotations

import asyncio

from niquests import (
    AsyncResponse,
    AsyncSession,
    ConnectionError,
    ConnectTimeout,
    Response,
)

from backend.core.logger import LOG


class AsyncTMDBClient:
    """Async client for The Movie Database (TMDB) API."""

    API_URL = "https://api.themoviedb.org/3"

    __slots__ = ("bearer_token", "session", "_active")

    def __init__(self, bearer_token: str) -> None:
        """Initialize TMDB client.

        Args:
            bearer_token: TMDB API bearer token
        """
        self.bearer_token = bearer_token
        self.session = AsyncSession()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.bearer_token}",
                "accept": "application/json",
            }
        )
        self._active = False

    async def __aenter__(self):
        """Enter async context manager."""
        self._active = True
        return self

    async def __aexit__(self, *args):
        """Ensure session is closed on exit."""
        self._active = False
        await self.session.close()

    def _ensure_active(self) -> None:
        if not self._active:
            raise RuntimeError(
                "TMDB client is not active. Use 'async with' context manager."
            )

    async def _make_request(
        self, mode: str, endpoint: str, **kwargs
    ) -> dict | None | bool:
        """Make HTTP request to TMDB API.

        Args:
            mode: HTTP method (GET, POST, etc.)
            endpoint: API endpoint
            **kwargs: Additional request parameters

        Returns:
            Parsed JSON response, None on failure, or False on 404
        """
        self._ensure_active()

        MAX_RETRIES = 5
        RETRY_DELAY = 2

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = await self.session.request(
                    mode, f"{self.API_URL}/{endpoint}", **kwargs
                )
                if resp.status == 404:
                    LOG.debug(f"404 Not Found for {endpoint}, skipping retries.")
                    return False
                resp.raise_for_status()
                return await resp.json()
            except (ConnectionError, ConnectTimeout) as e:
                if attempt == MAX_RETRIES:
                    LOG.warning(f"Failed to get data from TMDB API ({endpoint} - {e}) ")
                    return None
                LOG.warning(
                    f"Retry {attempt}/{MAX_RETRIES} for {endpoint} due to client or timeout error."
                )
            await asyncio.sleep(RETRY_DELAY)

        return None

    async def get_movie_details(self, tmdb_id: int) -> dict | None | bool:
        """Get movie details by TMDB ID.

        Args:
            tmdb_id: TMDB movie ID

        Returns:
            Parsed JSON response, None on failure, or False on 404
        """
        return await self._make_request("GET", f"movie/{tmdb_id}")

    async def get_tv_details(self, tmdb_id: int) -> dict | None | bool:
        """Get TV show details by TMDB ID.

        Args:
            tmdb_id: TMDB TV show ID

        Returns:
            Parsed JSON response, None on failure, or False on 404
        """
        return await self._make_request("GET", f"tv/{tmdb_id}")

    @staticmethod
    async def single_shot_request(
        mode: str,
        url: str,
        bearer_token: str,
        max_retries: int = 5,
        retry_delay: int = 2,
        **kwargs,
    ) -> Response | AsyncResponse | None | bool:
        """Make a single-shot TMDB API request without persistent session.

        Args:
            mode: HTTP method (GET, POST, etc.)
            url: Full API URL
            bearer_token: TMDB API bearer token
            max_retries: Maximum number of retries on failure
            retry_delay: Delay between retries in seconds
            **kwargs: Additional request parameters
        Returns:
            AsyncResponse, None on failure, or False on 404
        """
        headers = {
            "Authorization": f"Bearer {bearer_token}",
            "accept": "application/json",
        }

        for attempt in range(1, max_retries + 1):
            try:
                async with AsyncSession(headers=headers) as req:
                    resp = await req.request(mode, url, **kwargs)
                    if resp.status == 404:
                        LOG.debug(f"404 Not Found for {url}, skipping retries.")
                        return False
                    resp.raise_for_status()
                    return resp
            except (ConnectionError, ConnectTimeout) as e:
                if attempt == max_retries:
                    LOG.warning(f"Failed to get data from TMDB API ({url} - {e}) ")
                    return None
                LOG.warning(
                    f"Retry {attempt}/{max_retries} for {url} due to client or timeout error."
                )
            await asyncio.sleep(retry_delay)

        return None
