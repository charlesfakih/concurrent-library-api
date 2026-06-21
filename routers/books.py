from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select


from database import SessionDep
from models import BookTable, LoanTable
from schemas import Book, BookResponse, Loan

router = APIRouter(prefix="/books", tags=["books"])

@router.post("", response_model=BookResponse, status_code=201)
async def create_book(book: Book, session: SessionDep):
    new_book = BookTable(**book.model_dump())
    session.add(new_book)
    await session.commit()
    await session.refresh(new_book)
    return BookResponse(
        id=new_book.id,
        title=new_book.title,
        author=new_book.author,
        total_copies=new_book.total_copies,
        available_copies=new_book.total_copies
        )


@router.get("/{book_id}", response_model=BookResponse)
async def get_book(book_id: UUID, session: SessionDep):
    book = await session.get(BookTable, book_id)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    stmt = select(func.count()).select_from(LoanTable).where(LoanTable.book_id == book_id,
                                                             LoanTable.returned.is_(False))
    available_copies = book.total_copies - await session.scalar(stmt)
    return BookResponse(
        id=book.id,
        title=book.title,
        author=book.author,
        total_copies=book.total_copies,
        available_copies=available_copies
    )

@router.post("/{book_id}/borrow", response_model=Loan, status_code=201)
async def borrow_copy(book_id: UUID, session: SessionDep):
    stmt = select(BookTable).where(BookTable.id == book_id).with_for_update()
    book = await session.scalar(stmt)
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    
    stmt = select(func.count()).select_from(LoanTable).where(LoanTable.book_id == book_id,
                                                             LoanTable.returned.is_(False))
    available_copies = book.total_copies - await session.scalar(stmt)
    if available_copies <= 0:
        raise HTTPException(status_code=409, detail="No copies available")
    loan = LoanTable(book_id=book_id, returned=False)
    session.add(loan)
    await session.commit()
    await session.refresh(loan)
    return Loan(
        id=loan.id,
        book_id=book_id,
        returned=False
    )