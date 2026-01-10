from pydantic import BaseModel

from backend.enums import Service


class ServiceConfigUpdate(BaseModel):
    service_type: Service
    base_url: str
    api_key: str
    enabled: bool
