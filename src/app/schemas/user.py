from pydantic import BaseModel
from datetime import datetime

class UserLoginRequest(BaseModel):
    username: str
    password: str

class UserLoginResponse(BaseModel):
    username: str
    role: str
    organization_id: int
    created_at: datetime
    access_token : str
    refresh_token : str