from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    status: Literal["open", "done"]
    created_at: datetime
    