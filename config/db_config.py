from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine(
    'postgresql://postgres:1305@localhost/blog',
    echo=True
)

Base = declarative_base()

# Bind the engine here
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()