import { API } from "../Chess/utils/api";
import type { AiLevel, OpponentRecommendation, RecommendationResponse } from "./recommendation";

export async function getRecommendations(token: string, top_n: number = 5): Promise<RecommendationResponse>
{
    const response = await fetch(`${API}/recommendations/opponents?top_n=${top_n}`, {
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
        throw new Error("Failed to fetch recommendations");
    }
    return response.json();
}

// Cosine similarity (-1..1) -> 0..100 %. null when there is no score yet.
export function toMatchPercent(score: number | null): number | null {
    if (score === null || Number.isNaN(score)) return null;
    return Math.max(0, Math.min(100, Math.round(((score + 1) / 2) * 100)));
}

// Same Elo ranges as backend/scripts/generate_bots.py, used if the backend does not send ai_level.
export function botLevel(bot: OpponentRecommendation): AiLevel {
    if (bot.ai_level) return bot.ai_level;
    if (bot.elo < 1000) return "easy";
    if (bot.elo < 1500) return "medium";
    return "hard";
}

// Starts a 5+0 game against the AI at the bot's level and returns the game id.
export async function startBotGame(token: string, bot: OpponentRecommendation): Promise<number>
{
    const response = await fetch(`${API}/games/`, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify({
            initial_time_seconds: 300,
            increment_seconds: 0,
            opponent_type: "ai",
            ai_difficulty: botLevel(bot),
        }),
    });
    if (!response.ok) {
        throw new Error("Could not start the game");
    }
    const game = await response.json();
    return game.id;
}

// export async function getRecommendations(token: string, top_n: number = 5): Promise<RecommendationResponse>
// {
//     const response = await fetch(`${API}/recommendations/opponents?top_n=${top_n}`,{
//         headers: { Authorization: `Bearer ${token}` },
//     });
//     if (!response.ok) {
//         throw new Error("Failed to fetch recommendations");
//     }
//     return response.json();
// };
    