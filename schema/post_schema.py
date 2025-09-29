from models.blog import Post
from pydantic import BaseModel

from typing import Optional


class PostCreate(BaseModel):
    title: str
    content: str
    published: bool = False
   



class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    published: Optional[bool] = None
