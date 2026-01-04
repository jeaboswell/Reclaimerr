from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class ExternalIDs:
    """External provider IDs for media items."""

    imdb: str | None
    tmdb: str | None
    tmdb_collection: str | None
    tvdb: str | None


@dataclass(slots=True, frozen=True)
class AggregatedMovieData:
    """Movie with aggregated watch data across all users."""

    id: str
    name: str
    year: int | None
    library_name: str
    added_at: datetime | None
    premiere_date: datetime | None
    external_ids: ExternalIDs | None
    # watch data
    view_count: int
    last_viewed_at: datetime | None
    never_watched: bool
    # jellyfin-specific (None for Plex)
    played_by_user_count: int | None = None
    # jellyfin-specific container info
    container: str | None = None


@dataclass(slots=True, frozen=True)
class AggregatedSeriesData:
    """Series with aggregated watch data across all users."""

    id: str
    name: str
    year: int | None
    library_name: str
    added_at: datetime | None
    premiere_date: datetime | None
    external_ids: ExternalIDs | None
    # watch data
    view_count: int
    last_viewed_at: datetime | None
    never_watched: bool
    # jellyfin-specific (None for Plex)
    played_by_user_count: int | None = None
