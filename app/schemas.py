from pydantic import BaseModel
from typing import Optional

class User (BaseModel):
    username: Optional[str] = None
    email: str
    password: str

class Transaction (BaseModel):
    id: Optional[int] = None
    date: str
    description: str
    category: str
    type: str
    amount: float