from pydantic import BaseModel

from backend.enums import ScheduleType


class TaskScheduleRequest(BaseModel):
    schedule_type: ScheduleType
    schedule_value: str
    enabled: bool
