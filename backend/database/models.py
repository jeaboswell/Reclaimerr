from __future__ import annotations

from datetime import datetime

from services import sonarr
from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    SmallInteger,
    String,
    Text,
    func,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)

from backend.enums import MediaType, Service, TaskStatus


class Base(MappedAsDataclass, DeclarativeBase):
    """Base class for all models."""

    pass


class ServiceConfig(Base):
    """
    Configuration for external services (Plex, Jellyfin, Radarr, Sonarr, Seerr).
    """

    __tablename__ = "service_configs"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, init=False, autoincrement=True
    )
    service_type: Mapped[Service] = mapped_column(Enum(Service), unique=True)
    base_url: Mapped[str] = mapped_column(String(255))
    api_key: Mapped[str] = mapped_column(String(255))
    enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    # service specific settings
    extra_settings: Mapped[dict | None] = mapped_column(JSON, default=None, init=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        init=False,
    )


class CleanupRule(Base):
    """User-defined cleanup rules for movies and series."""

    __tablename__ = "cleanup_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)
    media_type: Mapped[MediaType] = mapped_column(Enum(MediaType))

    # rule criteria
    unwatched_days: Mapped[int | None] = mapped_column(Integer, default=None)
    last_watched_days: Mapped[int | None] = mapped_column(Integer, default=None)
    max_imdb_rating: Mapped[float | None] = mapped_column(Float, default=None)
    min_file_size_gb: Mapped[float | None] = mapped_column(Float, default=None)

    # actions
    auto_tag: Mapped[bool] = mapped_column(Boolean, default=True)

    # series-specific
    delete_partial_seasons: Mapped[bool] = mapped_column(Boolean, default=False)
    ended_series_grace_days: Mapped[int | None] = mapped_column(Integer, default=None)

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), init=False
    )


class Movie(Base):
    """Movie availability and metadata."""

    __tablename__ = "movies"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, init=False, autoincrement=True
    )

    # basic info
    title: Mapped[str] = mapped_column(String(512))
    year: Mapped[int] = mapped_column(SmallInteger)
    tmdb_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    # file info
    size: Mapped[int | None] = mapped_column(Integer, default=None)

    # external IDs
    radarr_id: Mapped[int | None] = mapped_column(
        Integer, unique=True, index=True, default=None
    )
    imdb_id: Mapped[str | None] = mapped_column(
        String(20), unique=True, index=True, default=None
    )

    # metadata info
    tmdb_title: Mapped[str | None] = mapped_column(String(512), default=None)
    original_title: Mapped[str | None] = mapped_column(String(512), default=None)
    tmdb_release_date: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    original_language: Mapped[str | None] = mapped_column(String(10), default=None)
    homepage: Mapped[str | None] = mapped_column(String(500), default=None)
    origin_country: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    poster_url: Mapped[str | None] = mapped_column(String(500), default=None)
    backdrop_url: Mapped[str | None] = mapped_column(
        String(500), default=None, init=False
    )
    overview: Mapped[str | None] = mapped_column(Text, default=None)
    genres: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    popularity: Mapped[float | None] = mapped_column(Float, default=None)
    vote_average: Mapped[float | None] = mapped_column(Float, default=None)
    vote_count: Mapped[int | None] = mapped_column(Integer, default=None)
    revenue: Mapped[int | None] = mapped_column(Integer, default=None)
    runtime: Mapped[int | None] = mapped_column(Integer, default=None)
    status: Mapped[str | None] = mapped_column(String(50), default=None)
    tagline: Mapped[str | None] = mapped_column(String(255), default=None)

    # watch tracking (from Plex/Jellyfin)
    last_viewed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    never_watched: Mapped[bool] = mapped_column(Boolean, default=True)

    # lifecycle tracking
    added_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), init=False
    )
    # we're only soft deleting data to maintain TMDB metadata on re-add
    removed_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, init=False
    )

    # cache freshness
    last_metadata_refresh_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, init=False
    )


class Series(Base):
    """Series availability and metadata."""

    __tablename__ = "series"

    id: Mapped[int] = mapped_column(
        Integer, primary_key=True, init=False, autoincrement=True
    )

    # basic info
    title: Mapped[str] = mapped_column(String(512))
    year: Mapped[int] = mapped_column(SmallInteger)
    tmdb_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)

    # file info
    size: Mapped[int | None] = mapped_column(Integer, default=None)

    # external IDs
    sonarr_id: Mapped[int | None] = mapped_column(
        Integer, unique=True, index=True, default=None
    )
    imdb_id: Mapped[str | None] = mapped_column(
        String(20), unique=True, index=True, default=None
    )
    tvdb_id: Mapped[str | None] = mapped_column(
        String(20), unique=True, index=True, default=None
    )

    # metadata info
    tmdb_title: Mapped[str | None] = mapped_column(String(512), default=None)
    original_title: Mapped[str | None] = mapped_column(String(512), default=None)
    tmdb_first_air_date: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    tmdb_last_air_date: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    original_language: Mapped[str | None] = mapped_column(String(10), default=None)
    homepage: Mapped[str | None] = mapped_column(String(500), default=None)
    origin_country: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    poster_url: Mapped[str | None] = mapped_column(String(500), default=None)
    backdrop_url: Mapped[str | None] = mapped_column(
        String(500), default=None, init=False
    )
    overview: Mapped[str | None] = mapped_column(Text, default=None)
    genres: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    popularity: Mapped[float | None] = mapped_column(Float, default=None)
    vote_average: Mapped[float | None] = mapped_column(Float, default=None)
    vote_count: Mapped[int | None] = mapped_column(Integer, default=None)
    status: Mapped[str | None] = mapped_column(String(50), default=None)
    tagline: Mapped[str | None] = mapped_column(String(255), default=None)

    # series-specific info
    season_count: Mapped[int | None] = mapped_column(Integer, default=None, init=False)

    # watch tracking (from Plex/Jellyfin)
    last_viewed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    view_count: Mapped[int] = mapped_column(Integer, default=0)
    never_watched: Mapped[bool] = mapped_column(Boolean, default=True)

    # lifecycle tracking
    added_at: Mapped[datetime | None] = mapped_column(
        DateTime, server_default=func.now(), init=False
    )
    # we're only soft deleting data to maintain TMDB metadata on re-add
    removed_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, init=False
    )

    # cache freshness
    last_metadata_refresh_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, init=False
    )


# class WatchHistory(Base):
#     """Watch history from Plex/Jellyfin - tracks when media was last watched."""

#     __tablename__ = "watch_history"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)

#     # foreign keys (one of these will be set)
#     movie_id: Mapped[int | None] = mapped_column(
#         ForeignKey("movies.id"), unique=True, default=None, init=False
#     )
#     series_id: Mapped[int | None] = mapped_column(
#         ForeignKey("series.id"), unique=True, default=None, init=False
#     )

#     # watch data - only what matters for cleanup decisions
#     last_viewed_at: Mapped[datetime | None] = mapped_column(
#         DateTime, default=None, init=False
#     )
#     view_count: Mapped[int] = mapped_column(Integer, default=0)

#     # relationships
#     movie: Mapped[Movie | None] = relationship(
#         back_populates="watch_history", default=None, init=False
#     )
#     series: Mapped[Series | None] = relationship(
#         back_populates="watch_history", default=None, init=False
#     )

#     synced_at: Mapped[datetime] = mapped_column(
#         DateTime, server_default=func.now(), init=False
#     )


# class CleanupCandidate(Base):
#     """Items identified as candidates for deletion based on cleanup rules."""

#     __tablename__ = "cleanup_candidates"

#     id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)

#     # foreign keys (one of these will be set)
#     movie_id: Mapped[int | None] = mapped_column(
#         ForeignKey("movies.id"), unique=True, default=None, init=False
#     )
#     series_id: Mapped[int | None] = mapped_column(
#         ForeignKey("series.id"), unique=True, default=None, init=False
#     )

#     # candidate info -> why it was marked (e.g., "Unwatched for 365 days")
#     reason: Mapped[str] = mapped_column(Text)
#     matched_rule_id: Mapped[int | None] = mapped_column(
#         ForeignKey("cleanup_rules.id"), default=None, init=False
#     )

#     # status
#     tagged_in_arr: Mapped[bool] = mapped_column(Boolean, default=False)
#     reviewed: Mapped[bool] = mapped_column(Boolean, default=False)  # user reviewed
#     approved_for_deletion: Mapped[bool] = mapped_column(Boolean, default=False)

#     # space savings
#     estimated_space_gb: Mapped[float | None] = mapped_column(
#         Float, default=None, init=False
#     )

#     created_at: Mapped[datetime] = mapped_column(
#         DateTime, server_default=func.now(), init=False
#     )
#     updated_at: Mapped[datetime] = mapped_column(
#         DateTime, server_default=func.now(), onupdate=func.now(), init=False
#     )

#     # relationships
#     movie: Mapped[Movie | None] = relationship(
#         back_populates="cleanup_candidate", default=None, init=False
#     )
#     series: Mapped[Series | None] = relationship(
#         back_populates="cleanup_candidate", default=None, init=False
#     )


class TaskRun(Base):
    """Track scheduled task execution history and status."""

    __tablename__ = "task_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, init=False)

    # scan_cleanup_candidates, sync_watch_history, etc.
    task_name: Mapped[str] = mapped_column(String(100))
    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus), default=TaskStatus.PENDING
    )

    # results
    items_processed: Mapped[int | None] = mapped_column(
        Integer, default=None, init=False
    )
    error_message: Mapped[str | None] = mapped_column(Text, default=None, init=False)

    started_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, init=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime, default=None, init=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), init=False
    )
