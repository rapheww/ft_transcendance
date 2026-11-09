import numpy as np

from sqlalchemy.orm import Session

from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity

from backend.models.user import User
from backend.ml.features import extract_player_profile

MAX_ELO_DIFFERENCE = 300
FEATURE_COLUMNS = [
    "elo", 
    "win_rate", 
    "bullet_ratio", 
    "blitz_ratio", 
    "rapid_ratio", 
    "classical_ratio", 
    "avg_game_length", 
    "games_played"
]

def get_player_profiles(db: Session) -> list[dict]:
    users = db.query(User).all()

    players = []

    for user in users:
        player = extract_player_profile(db, user.id)
        player["user_id"] = user.id
        players.append(player)

    return players

def split_candidates(players: list, user_id: int):
    humans = []
    bots = []

    for player in players:
        if player["user_id"] == user_id:
            continue
        if player["is_bot"]:
            bots.append(player)
        else:
            humans.append(player)
    return humans, bots

def filter_by_elo(candidates: list, target_elo: int, max_difference: int=300):
    return [
        player
        for player in candidates
        if abs(player["elo"] - target_elo) <= max_difference
    ]

def recommend_opponents(all_players: list, candidates: list, target: dict, top_n: int = 5):
    def to_row(p):
        return [p[c] for c in FEATURE_COLUMNS]

    scaler = StandardScaler().fit([to_row(p) for p in all_players])

    target_vec = scaler.transform([to_row(target)])
    cand_matrix = scaler.transform([to_row(p) for p in candidates])

    sims = np.clip(cosine_similarity(target_vec, cand_matrix)[0], -1.0, 1.0)

    ranked = sorted(
        ({**p, "similarity_score": float(s)} for p, s in zip(candidates, sims)),
        key=lambda p: p["similarity_score"],
        reverse=True,
    )
    return ranked[:top_n]

def recommend_with_rules(db: Session, user_id: int, top_n:int=5):
    players = get_player_profiles(db)
    target = next(
        (player for player in players
         if player["user_id"] == user_id),
         None
    )
    if target is None:
        return {"humans": [], "bots": []}

    humans, bots = split_candidates(players, user_id)
    humans = filter_by_elo(humans,target["elo"], MAX_ELO_DIFFERENCE)
    bots = filter_by_elo(bots, target["elo"], MAX_ELO_DIFFERENCE)
    human_group = [target] + humans
    bot_group = [target] + bots
    if target["games_played"] == 0:
        ranked_humans = sorted(
            humans,
            key=lambda player: abs(player["elo"] - target["elo"])
        )
        ranked_bots = sorted(
            bots,
            key=lambda player: abs(player["elo"] - target["elo"])
        )
        ranked_humans = [
            {**player, "similarity_score": None}
            for player in ranked_humans
        ]
        ranked_bots = [
            {**player, "similarity_score": None}
            for player in ranked_bots
        ]
    else:
        ranked_humans = recommend_opponents(players, humans, target, top_n) if humans else []
        ranked_bots = recommend_opponents(players, bots, target, top_n) if bots else []
    return {
        "humans": ranked_humans[:top_n],
        "bots": ranked_bots[:top_n]
    }

if __name__  == "__main__":

    from backend.db.session import SessionLocal

    with SessionLocal() as db:
        ranked = recommend_with_rules(db, user_id=1, top_n=5)
        print(ranked)
