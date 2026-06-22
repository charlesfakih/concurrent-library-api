from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import select

from config import ALGORITHM, SECRET_KEY, create_access_token
from database import SessionDep
from models import UserTable
from schemas import LoginResponse, UserResponse, UserRequest
import bcrypt
import jwt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
router = APIRouter(prefix="/auth", tags=["auth"])

def get_current_user(token: str = Depends(oauth2_scheme)) -> str:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user_id
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/users", response_model=UserResponse)
async def create_user(req: UserRequest, session: SessionDep):
    new_user = UserTable(email=req.email, hashed_password=hash_password(req.password))
    session.add(new_user)
    await session.commit()
    await session.refresh(new_user)
    return UserResponse(
        id=new_user.id,
        email=new_user.email
    )

@router.post("/login", response_model=LoginResponse)
async def login(session: SessionDep, req: OAuth2PasswordRequestForm = Depends()):
    stmt = select(UserTable).where(UserTable.email == req.username)
    stored_user = await session.scalar(stmt)
    if stored_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    success = verify_password(req.password, stored_user.hashed_password)
    if not success:
        raise HTTPException(status_code=401, detail="Wrong password")
    response = create_access_token(str(stored_user.id))
    return LoginResponse (
        access_token=response
    )