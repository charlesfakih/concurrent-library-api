
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
