from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import os



DATABASE_URL = os.getenv("POSTGRES_URT")
if not DATABASE_URL:
    raise ValueError("POSTGRES_URL not found in .env")

engine = create_engine(DATABASE_URL, echo=True)

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
