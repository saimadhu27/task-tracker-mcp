from datetime import datetime, date
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict

Priority = Literal["low", "medium", "high"]
PRIORITIES = get_args(Priority)

class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    status: Literal["open", "done"]
    priority: Priority
    due_date: date | None
    created_at: datetime
    