from datetime import datetime

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


class SessionCreate(BaseModel):
    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class SessionOut(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
