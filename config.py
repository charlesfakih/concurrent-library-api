import os
SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-secret-change-me")
ALGORITHM = "HS256"

from datetime import datetime, timedelta, timezone
import jwt

def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=30)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)