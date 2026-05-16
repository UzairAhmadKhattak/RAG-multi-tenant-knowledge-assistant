
from pydantic import BaseModel
from typing import Optional

class GeneralResponse(BaseModel):
    detail: str