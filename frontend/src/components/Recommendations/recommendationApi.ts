import type { RecommendationResponse } from "./recommendation";


export async function getRecommendations(token: string, top_n: number = 5): Promise<RecommendationResponse>
{
    const response = await fetch(`http://127.0.0.1:8000/api/recommendations/opponents?top_n=${top_n}`,{
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
        throw new Error("Failed to fetch recommendations");
    }
    return response.json();
};
    