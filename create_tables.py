from backend.db.base import Base
from backend.db.session import engine
from backend.models.user import User

Base.metadata.create_all(bind=engine)

print("Tables created.")