from pydantic import BaseModel, Field
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

class Message (BaseModel):
    role: Optional[str] = None
    message: str

class AgentReply (BaseModel):
    id: int = Field(descrition="Continue with the serial numbers or make the random number.")
    role: str = "ai"
    message: str = Field(description="Only contain your answer.")
    