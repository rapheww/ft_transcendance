export type AiLevel = "easy" | "medium" | "hard";

export interface OpponentRecommendation {
    user_id: number;
    username: string;
    elo: number;
    is_bot: boolean;
    // Optional: only sent if the backend adds it. Otherwise we guess it from the Elo.
    ai_level?: AiLevel | null;
    // Cosine similarity between -1 and 1, or null if the user has no finished game yet.
    similarity_score: number | null;
}

export interface RecommendationResponse {
    humans: OpponentRecommendation[];
    bots: OpponentRecommendation[];
}