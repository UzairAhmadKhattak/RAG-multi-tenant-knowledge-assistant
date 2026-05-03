
from pydantic import BaseModel
from typing import Optional

class GeneralResponse(BaseModel):
    message: str
    status_code: int
    error: Optional[str] = None