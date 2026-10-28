from sqlalchemy.orm import Session
from backend.db.session import SessionLocal
from backend.models.notification import Notification
from backend.websocket.notification_manager import notification_manager
from backend.services.user_service import create_user, update_user

def create_notification(db: Session, 
                        user_id: int, 
                        action: str, 
                        entity_type: str, 
                        message: str) -> Notification:
    notification = Notification(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        message=message,
        is_read=False,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)

    return notification

def get_notifications(db: Session, user_id: int):
    return (db.query(Notification)
            .filter(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .all()
    )

def mark_as_read(db: Session, notification_id: int, user_id: int):
    notification = (db.query(Notification)
                    .filter(Notification.id == notification_id,
                            Notification.user_id == user_id,)
                    .first()
    )

    if notification is None:
        return None
    
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification

async def notify_user(db: Session,
                user_id: int,
                action: str,
                entity_type: str,
                message: str):
    notification = create_notification(db, 
                                       user_id, 
                                       action, 
                                       entity_type,
                                       message)
    await notification_manager.send(
        user_id,
        {
            "type": "notification",
            "id": notification.id,
            "action": notification.action,
            "entity_type": notification.entity_type,
            "message": notification.message,
            "is_read": notification.is_read,
        }                         
    )
    return notification

if __name__ == "__main__":
    with SessionLocal() as db:
        notification = create_notification(db, 1, "create", "tournament", "Tournament is ready")
        print("notificaion id : ", notification.id)
        print("user id: ", notification.user_id)
        print("action : ", notification.action)
        print("entity_type : ", notification.entity_type)
        print("message : ", notification.message)
        notifications = get_notifications(db, 1)
        is_read = mark_as_read(db, 2, 1)
        if is_read:
            print("after change: ", notification.is_read)
        print("Print all user ids and is_read")
        for notification in notifications:
            print(f"user_id : {notification.user_id} is_read: {notification.is_read}")
        
    
