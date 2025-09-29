from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String
from config.db_config import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    posts = relationship("Post", back_populates="owner", cascade="all, delete-orphan")
