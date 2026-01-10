from enum import Enum


class LogSource(Enum):
    """
    Enum to control tag for frontend vs backend
    FE: Frontend
    BE: Backend
    """

    FE = "[FE]"
    BE = "[BE]"
