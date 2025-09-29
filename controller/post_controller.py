from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from models.blog import Post
from schema.post_schema import PostCreate
from config.db_config import get_db
from controller.user_controller import get_current_user

post_router = APIRouter()

@post_router.post("/create", response_model=PostCreate)
async def create_post(
    post: PostCreate,
    db: AsyncSession = Depends(get_db),
    current_user: int = Depends(get_current_user) 
):
    new_post = Post(
        title=post.title,
        content=post.content,
        published=post.published,
        owner_id=current_user  
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post)
    return new_post
