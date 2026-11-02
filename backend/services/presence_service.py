from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from backend.models.user import User

ONLINE_WINDOW = timedelta(seconds=90)


def record_heartbeat(db: Session, user: User) -> datetime:
    last_seen_at = datetime.now(timezone.utc)
    user.last_seen_at = last_seen_at
    db.commit()
    return last_seen_at


def is_online(last_seen_at: datetime | None,
              *, now: datetime | None = None) -> bool:
    if last_seen_at is None:
        return False

    now = now or datetime.now(timezone.utc)
    if last_seen_at.tzinfo is None:
        last_seen_at = last_seen_at.replace(tzinfo=timezone.utc)

    return now - ONLINE_WINDOW <= last_seen_at <= now
