from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import ForeignKey
from uuid import UUID, uuid4

class Base(DeclarativeBase):
    pass

class BookTable(Base):
    __tablename__ = "books"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    title: Mapped[str] = mapped_column()
    author: Mapped[str] = mapped_column()
    total_copies: Mapped[int] = mapped_column()

class LoanTable(Base):
    __tablename__= "loans"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    book_id: Mapped[UUID] = mapped_column(ForeignKey("books.id", ondelete="RESTRICT"))
    returned: Mapped[bool] = mapped_column(default=False)
    