from fastapi import FastAPI
from config.db_config import engine,Base
from models.user import User
from models.blog import Post
from controller.user_controller import user_router
from controller.post_controller import post_router
from fastapi.middleware.cors import CORSMiddleware
Base.metadata.create_all(bind=engine)


app=FastAPI()





origins = [
    "http://localhost:5000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def main():
    return {"message": "Hello World"}
@app.get("/test")
async def hello():
    return {"message": "Hello World"}

app.include_router(user_router, prefix="/users", tags=["users"])

app.include_router(post_router, prefix="/posts", tags=["posts"])