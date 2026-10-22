import random

from sqlalchemy.orm import Session

from backend.models.user import User
from backend.db.session import SessionLocal

BOT_LEVELS = {
    "easy": {
        "count": 10,
        "elo_min": 600,
        "elo_max": 1000,
    },
    "medium": {
        "count": 12,
        "elo_min": 1000,
        "elo_max": 1500,
    },
    "hard": {
        "count": 10,
        "elo_min": 1500,
        "elo_max": 2000,
    },
}

TIME_CONTROLS = ["fast", "normal", "slow"]

STYLE_DISTRIBUTION = {
    "easy": [
        "aggressive",
        "aggressive",
        "aggressive",
        "balanced",
        "balanced",
        "balanced",
        "balanced",
        "defensive",
        "defensive",
        "defensive",
    ],

    "medium": [
        "aggressive",
        "aggressive",
        "aggressive",
        "aggressive",
        "balanced",
        "balanced",
        "balanced",
        "balanced",
        "defensive",
        "defensive",
        "defensive",
        "defensive",
    ],

    "hard": [
        "aggressive",
        "aggressive",
        "aggressive",
        "balanced",
        "balanced",
        "balanced",
        "balanced",
        "defensive",
        "defensive",
        "defensive",
    ],
}

def generate_bot_data(index: int, level: str, style: str, config: dict):
    username = f"bot_{index:03d}"
    return {
        "username": username,
        "email": f"{username}@bots.invalid",
        "password_hash": "!",
        "is_bot": True,
        "ai_level": level,
        "style": style,
        "elo": random.randint(config["elo_min"], 
                              config["elo_max"],),
        "preferred_time_control": random.choice(TIME_CONTROLS)
    }

def generate_all_bots():
    bots = []
    index = 1

    for level, config in BOT_LEVELS.items():
        styles = STYLE_DISTRIBUTION[level]

        for style in styles:
            bot = generate_bot_data(index,
                                    level,
                                    style,
                                    config,)
            bots.append(bot)
            index += 1
    return bots

def seed_bots(db: Session):
    bots = generate_all_bots()

    for bot_data in bots:
        existing = (db.query(User)
                    .filter(User.username == bot_data["username"])
                    .first())
        if existing:
            continue
        bot = User(**bot_data)
        db.add(bot)

    db.commit()

if __name__ == "__main__":
    with SessionLocal() as db:
        seed_bots(db)
    print("Bot seeding completed.")