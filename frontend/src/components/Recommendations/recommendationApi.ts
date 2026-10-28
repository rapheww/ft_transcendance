import { API } from "../Chess/utils/api";
import type { RecommendationResponse } from "./recommendation";


export async function getRecommendations(token: string, top_n: number = 5): Promise<RecommendationResponse>
{
    const response = await fetch(`${API}/recommendations/opponents?top_n=${top_n}`,{
        headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) {
        throw new Error("Failed to fetch recommendations");
    }
    return response.json();
};
    