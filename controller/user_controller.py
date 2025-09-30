from fastapi import APIRouter, Depends, HTTPException,Response,Request
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
import os
from dotenv import load_dotenv
dotnev=os.path.join(os.path.dirname(__file__), '.env')

load_dotenv()

user_router = APIRouter()

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY")
REFRESH_SECRET_KEY = os.getenv("REFRESH_SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES =  30 
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# utility: create token
def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# utility: create refresh token
def create_refresh_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm=ALGORITHM)

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
def login(user: UserLogin,response:Response, db: Session = Depends(get_db)):
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
    refresh_token = create_refresh_token({"sub": db_user.email, "user_id": db_user.id})
    response.set_cookie(key="access_token",
                        
        value=token,
        httponly=True,
        secure=True,   
        samesite="lax")
    response.set_cookie(key="refresh_token",
                        value=refresh_token,
                        httponly=True,
                        secure=True,   
                        samesite="lax")

    return {"access_token": token, "token_type": "bearer","refresh_token": refresh_token}

# ---------------- LOGOUT ----------------

@user_router.post("/logout")
def logout(response:Response,token: str = Depends(oauth2_scheme)):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
   
    return {"message": "Logged out successfully"}

# ---------------- PROTECTED ROUTE ----------------
# refresh token
@user_router.post("/refresh")
def refresh_token(request: Request, response: Response, db: Session = Depends(get_db)):
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")

    try:
        payload = jwt.decode(refresh_token, REFRESH_SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        stmt = select(User).where(User.id == user_id)
        result = db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        new_access_token = create_access_token({"sub": user.email, "user_id": user.id})
        response.set_cookie(key="access_token",
                            value=new_access_token,
                            httponly=True,
                            secure=True,   
                            samesite="lax")
        return {"access_token": new_access_token, "token_type": "bearer"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")


def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Token missing")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("user_id")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Access token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    stmt = select(User).where(User.id == user_id)
    result = db.execute(stmt)
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
