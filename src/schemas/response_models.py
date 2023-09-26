from typing import Optional

from pydantic import BaseModel


class JsonEntity(BaseModel):
    body: dict[str, str]
    status_code: Optional[int] = 200
