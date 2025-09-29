from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from models.user import User
from schema.user_schema import UserCreate, Userlogin as UserLogin
from config.db_config import get_db
from pwdlib import PasswordHash
import jwt
from datetime import datetime, timedelta
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError

user_router = APIRouter()

# JWT settings
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# utility: create token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# ---------------- REGISTER ----------------
@user_router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    stmt = select(User).where(User.email == user.email)
    result = db.execute(stmt)  
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    password_hash = PasswordHash.recommended()
    new_user = User(
        username=user.username,
        email=user.email,
        full_name=user.full_name,
        hashed_password=password_hash.hash(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {"message": "User registered successfully", "user": new_user}

# ---------------- LOGIN ----------------
@user_router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    stmt = select(User).where(User.email == user.email)
    result = db.execute(stmt)  
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(status_code=400, detail="Invalid credentials")

    password = PasswordHash.recommended()
    if not password.verify(user.password, db_user.hashed_password):
        raise HTTPException(status_code=400, detail="Invalid credentials")

    # create token
    token = create_access_token({"sub": db_user.email, "user_id": db_user.id})

    return {"access_token": token, "token_type": "bearer"}

# ---------------- LOGOUT ----------------
# JWT is stateless, so we can’t really “invalidate” tokens unless we use a blacklist.
# Simple approach: logout on frontend by deleting token
blacklist = set()

@user_router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):
    blacklist.add(token)
    return {"message": "Logged out successfully"}

# ---------------- PROTECTED ROUTE ----------------
@user_router.get("/me")
def get_me(token: str = Depends(oauth2_scheme)):
    if token in blacklist:
        raise HTTPException(status_code=401, detail="Token has been revoked")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"user": payload}
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        stmt = select(User).where(User.id == user_id)
        result = db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user  # return full user object
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
