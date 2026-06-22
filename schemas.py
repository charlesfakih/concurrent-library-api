
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class Book(BaseModel):
    title: str
    author: str
    total_copies: int = Field(gt=0, description="Must be at least one copy")

class BookResponse(Book):
    id: UUID = Field(default_factory=uuid4)
    available_copies: int

class Loan(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    book_id: UUID
    returned: bool = False
    user_id: UUID

class UserBase(BaseModel):
    email: str

class UserRequest(UserBase):
    password: str

class UserResponse(UserBase):
    id: UUID = Field(default_factory=uuid4)

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")