from enum import Enum, auto


class Service(Enum):
    SONARR = auto()
    RADARR = auto()
    JELLYFIN = auto()
    PLEX = auto()
    SEERR = auto()


class MediaType(Enum):
    MOVIE = auto()
    SERIES = auto()


class SeriesStatus(Enum):
    CONTINUING = auto()
    ENDED = auto()


class TaskStatus(Enum):
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
