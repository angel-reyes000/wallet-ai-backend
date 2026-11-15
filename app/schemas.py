from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import date
import math
from app.validation import (
    EMAIL_RE, COLOR_RE, DATE_RE, MONTH_RE, MIN_YEAR, MAX_YEAR, MAX_AMOUNT, clean
)

# Custom messages are raised as ValueError: the handler in main.py sends them as-is to the front.

class User (BaseModel):
    """Sign up."""
    username: str
    email: str
    password: str

    @field_validator("username")
    @classmethod
    def validateUsername (cls, value: str):
        value = clean(value)
        if not 2 <= len(value) <= 100:
            raise ValueError("Username must have between 2 and 100 characters.")
        return value

    @field_validator("email")
    @classmethod
    def validateEmail (cls, value: str):
        value = clean(value).lower()
        if len(value) > 100 or not EMAIL_RE.match(value):
            raise ValueError("Invalid email address.")
        return value

    @field_validator("password")
    @classmethod
    def validatePassword (cls, value: str):
        if len(value) < 8:
            raise ValueError("Password must have at least 8 characters.")
        # bcrypt only reads the first 72 bytes
        if len(value.encode("utf-8")) > 72:
            raise ValueError("Password must have at most 72 bytes.")
        if not value.strip():
            raise ValueError("Password can not be only spaces.")
        return value

class LoginUser (BaseModel):
    """Log in: lenient with the password so older accounts keep working."""
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validateEmail (cls, value: str):
        value = clean(value)
        if not value or len(value) > 100:
            raise ValueError("Invalid email address.")
        return value

    @field_validator("password")
    @classmethod
    def validatePassword (cls, value: str):
        if not value or len(value) > 128:
            raise ValueError("Invalid password.")
        return value

class Transaction (BaseModel):
    id: Optional[int] = Field(default=None, gt=0)
    date: str
    description: str
    category: str
    card: str
    amount: float = Field(allow_inf_nan=False)

    @field_validator("date")
    @classmethod
    def validateDate (cls, value: str):
        value = clean(value)
        if not DATE_RE.match(value):
            raise ValueError("Date must have the format YYYY-MM-DD.")
        try:
            parsed = date.fromisoformat(value)
        except ValueError:
            raise ValueError("Invalid date.")
        if not MIN_YEAR <= parsed.year <= MAX_YEAR:
            raise ValueError(f"Date year must be between {MIN_YEAR} and {MAX_YEAR}.")
        return value

    @field_validator("description")
    @classmethod
    def validateDescription (cls, value: str):
        value = clean(value)
        if not 1 <= len(value) <= 500:
            raise ValueError("Description must have between 1 and 500 characters.")
        return value

    @field_validator("category", "card")
    @classmethod
    def validateShortText (cls, value: str):
        value = clean(value)
        if not 1 <= len(value) <= 30:
            raise ValueError("Category and card must have between 1 and 30 characters.")
        return value

    @field_validator("amount")
    @classmethod
    def validateAmount (cls, value: float):
        if math.isnan(value) or value == 0:
            raise ValueError("Amount can not be 0.")
        if abs(value) > MAX_AMOUNT:
            raise ValueError("Amount is too large.")
        return round(value, 2)

class Message (BaseModel):
    role: Optional[str] = None
    message: str

    @field_validator("message")
    @classmethod
    def validateMessage (cls, value: str):
        value = clean(value)
        if not value:
            raise ValueError("Message can not be empty.")
        if len(value) > 2000:
            raise ValueError("Message must have at most 2000 characters.")
        return value

class AgentReply (BaseModel):
    role: str = "ai"
    message: str = Field(description="Only contain the all answer.")

class Card(BaseModel):
    id: Optional[int] = Field(default=None, gt=0)
    name: str
    type: str
    last_numbers: str
    expired_date: str
    background_color: str
    color: str
    user_id: Optional[str] = None

    @field_validator("name")
    @classmethod
    def validateName (cls, value: str):
        value = clean(value)
        if not 1 <= len(value) <= 30:
            raise ValueError("Card name must have between 1 and 30 characters.")
        if value.lower() == "cash":
            raise ValueError("\"Cash\" is reserved, choose another card name.")
        return value

    @field_validator("type")
    @classmethod
    def validateType (cls, value: str):
        value = clean(value)
        if value not in ("Credit", "Debit"):
            raise ValueError("Card type must be Credit or Debit.")
        return value

    @field_validator("last_numbers")
    @classmethod
    def validateLastNumbers (cls, value: str):
        value = clean(value)
        if not (len(value) == 4 and value.isascii() and value.isdigit()):
            raise ValueError("Last digits must be exactly 4 numbers.")
        return value

    @field_validator("expired_date")
    @classmethod
    def validateExpiredDate (cls, value: str):
        # accepts "YYYY-MM" (month input) or a full date and keeps "YYYY-MM"
        value = clean(value)[:7]
        if not MONTH_RE.match(value):
            raise ValueError("Expiration date must have the format YYYY-MM.")
        year, month = int(value[:4]), int(value[5:7])
        if not (1 <= month <= 12 and MIN_YEAR <= year <= MAX_YEAR):
            raise ValueError("Invalid expiration date.")
        return value

    @field_validator("background_color", "color")
    @classmethod
    def validateColor (cls, value: str):
        value = clean(value)
        if not COLOR_RE.match(value):
            raise ValueError("Invalid color.")
        return value

class UserSettings (BaseModel):
    temperature: float = Field(default=0.5, ge=0, le=1)
    theme: Literal["dark", "light"] = "dark"
