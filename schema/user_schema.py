from models.user import User
from pydantic import BaseModel



class UserCreate(BaseModel):
    username: str
    email: str
    full_name: str | None = None
    password: str

    
class Userlogin(BaseModel):
    email: str
    password: str