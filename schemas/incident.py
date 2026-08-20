from datetime import datetime

from pydantic import BaseModel


class Incident(BaseModel):
    incident_id: str
    service: str
    description: str
    started_at: datetime