from uuid import UUID

from fastapi import APIRouter, HTTPException
from sqlalchemy import select

from database import SessionDep
from models import LoanTable
from schemas import Loan

router = APIRouter(prefix="/loans", tags=["loans"])

@router.post("/{loan_id}/return", response_model=Loan)
async def return_copy(loan_id: UUID, session: SessionDep):
    stmt = select(LoanTable).where(LoanTable.id == loan_id).with_for_update()
    loan = await session.scalar(stmt)
    if loan is None:
        raise HTTPException(status_code=404, detail="Loan not found")
    if loan.returned == True:
        raise HTTPException(status_code=409, detail="Already returned")
    loan.returned = True
    await session.commit()
    await session.refresh(loan)
    return Loan(
        id=loan.id,
        book_id=loan.book_id,
        returned=loan.returned
    )