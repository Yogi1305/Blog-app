from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.blog import Post
from schema.post_schema import PostCreate,PostUpdate
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
        published=False,
        owner_id=current_user.id  
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post

# get all public posts
@post_router.get("/post")
async def get_posts(db: AsyncSession = Depends(get_db)):
    result = db.execute(select(Post).where(Post.published == True))
    posts = result.scalars().all()
    return posts
# make post public or private
@post_router.put("/{post_id}/publish")
async def publish_post(post_id: int, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    print(current_user.id, post_id)
    result = db.execute(select(Post).where(Post.id == post_id, Post.owner_id == current_user.id))
    post = result.scalar_one_or_none()
    if not post:
        return {"error": "Post not found or you're not the owner"}
    post.published = not post.published
    db.commit()
    db.refresh(post)
    return {"message": f"Post {'published' if post.published else 'unpublished'} successfully", "post": post}
# get all posts of the logged-in user
@post_router.get("/myposts")
async def get_my_posts(db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    result = db.execute(select(Post).where(Post.owner_id == current_user.id))
    posts = result.scalars().all()
    return posts
# update a post
@post_router.put("/{post_id}/update")
async def update_post(post_id: int, post_data: PostUpdate, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    result = db.execute(select(Post).where(Post.id == post_id, Post.owner_id == current_user.id))
    post = result.scalar_one_or_none()
    if not post:
        return {"error": "Post not found or you're not the owner"}
    if not post_data.title and not post_data.content:
        return {"error": "No data provided for update"}
    post.title = post_data.title if post_data.title else post.title
    post.content = post_data.content if post_data.content else post.content
  
    db.commit()
    db.refresh(post)
    return {"message": "Post updated successfully", "post": post}

# delete a post
@post_router.delete("/{post_id}/delete")
async def delete_post(post_id: int, db: AsyncSession = Depends(get_db), current_user: int = Depends(get_current_user)):
    result = db.execute(select(Post).where(Post.id == post_id, Post.owner_id == current_user.id))
    post = result.scalar_one_or_none()
    if not post:
        return {"error": "Post not found or you're not the owner"}
    db.delete(post)
    db.commit()
    return {"message": "Post deleted successfully"}