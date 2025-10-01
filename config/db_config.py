from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv
load_dotenv()
import os




DATABASE_URL = os.getenv("POSTGRES_URT")
print(f"DATABASE_URL",DATABASE_URL)
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
