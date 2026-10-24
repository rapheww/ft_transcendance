export interface OpponentRecommendation {
    user_id: number;
    username: string;
    elo: number;
    is_bot: boolean;
    similarity_score: number | null;
}

export interface RecommendationResponse {
    humans: OpponentRecommendation[];
    bots: OpponentRecommendation[];
}