from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from backend.db.base import Base

class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    action: Mapped[str] = mapped_column(String(20), nullable=False)

    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)

    message: Mapped[str] = mapped_column(String(255), nullable=False)

    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


# action
# → create / update / delete

# entity_type
# → game / tournament / profile / friend / etc.