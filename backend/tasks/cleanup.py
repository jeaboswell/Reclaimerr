from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.logger import LOG
from backend.core.service_manager import service_manager
from backend.database.database import get_db
from backend.database.models import CleanupCandidate, CleanupRule, Movie, Series
from backend.enums import MediaType


async def scan_cleanup_candidates() -> None:
    """
    Scan media libraries and identify cleanup candidates based on configured rules.
    """
    LOG.info("Starting cleanup candidates scan")

    try:
        async for db in get_db():
            await _scan_with_db(db)
            break

    except Exception as e:
        LOG.error(f"Error scanning cleanup candidates: {e}", exc_info=True)
        raise


async def _scan_with_db(db: AsyncSession) -> None:
    """Internal method to perform scan with database session."""
    try:
        # load all enabled cleanup rules
        result = await db.execute(
            select(CleanupRule).where(CleanupRule.enabled == True)
        )
        rules = result.scalars().all()

        if not rules:
            LOG.info("No enabled cleanup rules found")
            return

        LOG.info(f"Found {len(rules)} enabled cleanup rules")

        # separate rules by media type
        movie_rules = [r for r in rules if r.media_type == MediaType.MOVIE]
        series_rules = [r for r in rules if r.media_type == MediaType.SERIES]

        candidates_created = 0
        candidates_updated = 0

        # process movies
        if movie_rules:
            created, updated = await _process_media(db, movie_rules, MediaType.MOVIE)
            candidates_created += created
            candidates_updated += updated

        # process series
        if series_rules:
            created, updated = await _process_media(db, series_rules, MediaType.SERIES)
            candidates_created += created
            candidates_updated += updated

        LOG.info(
            f"Cleanup scan completed: {candidates_created} new candidates, "
            f"{candidates_updated} updated"
        )
    except Exception:
        raise


async def _process_media(
    db: AsyncSession, rules: list[CleanupRule], media_type: MediaType
) -> tuple[int, int]:
    """
    Process movies or series against cleanup rules.

    Returns (created_count, updated_count)
    """
    # get all media items
    if media_type == MediaType.MOVIE:
        result = await db.execute(select(Movie).where(Movie.removed_at.is_(None)))
        media_items = result.scalars().all()
        id_field = "movie_id"
    else:
        result = await db.execute(select(Series).where(Series.removed_at.is_(None)))
        media_items = result.scalars().all()
        id_field = "series_id"

    LOG.info(f"Processing {len(media_items)} {media_type.value} items")

    candidates_created = 0
    candidates_updated = 0

    for item in media_items:
        # evaluate all rules against this item
        matched_rules = []
        matched_criteria = {}
        reasons = []

        for rule in rules:
            if _evaluate_rule(item, rule, matched_criteria, reasons):
                matched_rules.append(rule.id)

        # if item matches at least one rule, create/update candidate
        if matched_rules:
            # check if candidate already exists
            result = await db.execute(
                select(CleanupCandidate).where(CleanupCandidate.id == item.id)
            )
            existing = result.scalar_one_or_none()

            combined_reason = "; ".join(reasons)

            # calculate space savings (convert bytes to GB)
            space_gb = item.size / (1024**3) if item.size else None

            if existing:
                # update existing candidate
                existing.matched_rule_ids = matched_rules
                existing.matched_criteria = matched_criteria
                existing.reason = combined_reason
                existing.estimated_space_gb = space_gb
                existing.updated_at = datetime.now(timezone.utc)
                candidates_updated += 1
            else:
                # create new candidate
                candidate_data = {
                    "media_type": media_type,
                    "matched_rule_ids": matched_rules,
                    "matched_criteria": matched_criteria,
                    "reason": combined_reason,
                    "estimated_space_gb": space_gb,
                }
                if id_field == "movie_id":
                    candidate_data["movie_id"] = item.id
                else:
                    candidate_data["series_id"] = item.id

                candidate = CleanupCandidate(**candidate_data)
                db.add(candidate)
                candidates_created += 1

                # auto-tag if enabled on any matched rule
                should_tag = False
                for rule_id in matched_rules:
                    rule = await db.get(CleanupRule, rule_id)
                    if rule and rule.auto_tag:
                        should_tag = True
                        break

                if should_tag:
                    await _auto_tag_item(item, media_type)

    return candidates_created, candidates_updated


def _evaluate_rule(
    item: Movie | Series, rule: CleanupRule, matched_criteria: dict, reasons: list[str]
) -> bool:
    """
    Evaluate if an item matches a cleanup rule.

    All non-null criteria must match (AND logic).
    Updates matched_criteria dict and reasons list if matched.

    Returns True if item matches rule.
    """
    # validate rule has at least one criterion set
    has_criteria = any(
        [
            rule.library_name is not None,
            rule.min_popularity is not None,
            rule.max_popularity is not None,
            rule.min_vote_average is not None,
            rule.max_vote_average is not None,
            rule.min_vote_count is not None,
            rule.max_vote_count is not None,
            rule.min_view_count is not None,
            rule.max_view_count is not None,
            rule.include_never_watched is not None,
            rule.min_days_since_added is not None,
            rule.max_days_since_added is not None,
            rule.min_size is not None,
            rule.max_size is not None,
        ]
    )

    if not has_criteria:
        LOG.warning(f"Rule '{rule.name}' has no criteria set, skipping")
        return False

    rule_reasons = []

    # always exclude items with no media (size = 0 or None)
    if not item.size or item.size == 0:
        return False

    # check library filtering
    if rule.library_name is not None and (item.library_name != rule.library_name):
        return False

    # check popularity
    if rule.min_popularity is not None and (
        item.popularity is None or item.popularity < rule.min_popularity
    ):
        return False
    if rule.max_popularity is not None and (
        item.popularity is None or item.popularity > rule.max_popularity
    ):
        return False
    if rule.min_popularity is not None or rule.max_popularity is not None:
        matched_criteria["popularity"] = item.popularity
        rule_reasons.append(f"Popularity {item.popularity}")

    # check vote average
    if rule.min_vote_average is not None and (
        item.vote_average is None or item.vote_average < rule.min_vote_average
    ):
        return False
    if rule.max_vote_average is not None and (
        item.vote_average is None or item.vote_average > rule.max_vote_average
    ):
        return False
    if rule.min_vote_average is not None or rule.max_vote_average is not None:
        matched_criteria["vote_average"] = item.vote_average
        rule_reasons.append(f"Rating {item.vote_average}/10")

    # check vote count
    if rule.min_vote_count is not None and (
        item.vote_count is None or item.vote_count < rule.min_vote_count
    ):
        return False
    if rule.max_vote_count is not None and (
        item.vote_count is None or item.vote_count > rule.max_vote_count
    ):
        return False
    if rule.min_vote_count is not None or rule.max_vote_count is not None:
        matched_criteria["vote_count"] = item.vote_count
        rule_reasons.append(f"{item.vote_count} votes")

    # check view count
    if rule.min_view_count is not None and item.view_count < rule.min_view_count:
        return False
    if rule.max_view_count is not None and item.view_count > rule.max_view_count:
        return False

    # check never watched flag
    # include_never_watched=True (default/None): Include both watched and never-watched (no filter)
    # include_never_watched=False: Exclude never-watched items (only watched items)
    if rule.include_never_watched is False:
        if item.never_watched:
            return False

    # log view/watch status if we're filtering by it
    if (
        rule.min_view_count is not None
        or rule.max_view_count is not None
        or rule.include_never_watched is False
    ):
        matched_criteria["view_count"] = item.view_count
        matched_criteria["never_watched"] = item.never_watched
        if item.never_watched:
            rule_reasons.append("Never watched")
        else:
            rule_reasons.append(f"Watched {item.view_count} time(s)")

    # check days since added
    if item.added_at:
        days_since_added = (
            datetime.now(timezone.utc) - item.added_at.replace(tzinfo=timezone.utc)
        ).days
        if (
            rule.min_days_since_added is not None
            and days_since_added < rule.min_days_since_added
        ):
            return False
        if (
            rule.max_days_since_added is not None
            and days_since_added > rule.max_days_since_added
        ):
            return False
        if (
            rule.min_days_since_added is not None
            or rule.max_days_since_added is not None
        ):
            matched_criteria["days_since_added"] = days_since_added
            rule_reasons.append(f"Added {days_since_added} days ago")

    # check size (bytes)
    if rule.min_size is not None and (item.size is None or item.size < rule.min_size):
        return False
    if rule.max_size is not None and (item.size is None or item.size > rule.max_size):
        return False
    if rule.min_size is not None or rule.max_size is not None:
        matched_criteria["size"] = item.size
        size_gb = item.size / (1024**3) if item.size else 0
        rule_reasons.append(f"Size {size_gb:.2f} GB")

    # all criteria matched!
    if rule_reasons:
        reasons.append(f"{rule.name}: {', '.join(rule_reasons)}")
    return True


async def _auto_tag_item(item: Movie | Series, media_type: MediaType):
    """
    Auto-tag an item in Radarr/Sonarr with cleanup candidate tag.
    """
    try:
        if media_type == MediaType.MOVIE and isinstance(item, Movie):
            if item.radarr_id:
                # TODO: Implement radarr.tag_movie() in service manager
                LOG.debug(
                    f"Would tag movie {item.title} in Radarr (not implemented yet)"
                )
        elif media_type == MediaType.SERIES and isinstance(item, Series):
            if item.sonarr_id:
                # TODO: Implement sonarr.tag_series() in service manager
                LOG.debug(
                    f"Would tag series {item.title} in Sonarr (not implemented yet)"
                )
    except Exception as e:
        LOG.warning(f"Failed to auto-tag {item.title}: {e}")


# async def auto_tag_candidates():
#     """
#     Automatically tag cleanup candidates in Radarr/Sonarr.

#     Can be called manually or as part of scan_cleanup_candidates.
#     """
#     LOG.info("Starting auto-tagging of cleanup candidates")

#     try:
#         # TODO: Implement auto-tagging logic
#         # 1. Get list of candidates from database
#         # 2. Create/get "vacuumarr-candidate" tag in Radarr/Sonarr
#         # 3. Add tag to each candidate movie/series

#         LOG.info("Auto-tagging completed successfully")
#     except Exception as e:
#         LOG.error(f"Error auto-tagging candidates: {e}", exc_info=True)
