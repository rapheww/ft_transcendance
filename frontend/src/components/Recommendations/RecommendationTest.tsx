import { useState, useEffect } from "react";
import type { RecommendationResponse } from "./recommendation";
import { getRecommendations } from "./recommendationApi";
import { useAuth } from "../AuthProvider";

export default function RecommendationTest() {
    const { token } = useAuth();

    const [recommendations, setRecommendations] = 
        useState<RecommendationResponse>({
        humans: [],
        bots: [],
    });

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let cancelled = false;
        async function loadRecommendations() {
            if (!token) {
                setRecommendations({ humans: [], bots: [] });
                setError(null);
                setLoading(false);
                return;
            }
            try {
                setLoading(true);
                setError(null);
                const data = await getRecommendations(token);
                if (!cancelled)
                    setRecommendations(data);
            } catch(err) {
                if (!cancelled) {
                    setError(err instanceof Error ? err.message : "Unknown error");
                }
            } finally {
                if (!cancelled) {
                    setLoading(false);
                }
            }
        }
        loadRecommendations();
        return () => {
            cancelled = true;
        };
    }, [token]);

     return (
        <div>
            <h2>RecommendationOpponents</h2>
            {loading && <p>Loading recommendations...</p>}
            {error && <p>error: {error}</p>}
            {!token && <p>Please log in to see recommendations.</p>}
            {token && !loading && !error && (
                <div>
                    <h3>Humans: {recommendations.humans.length}</h3>
                    {recommendations.humans.map((player) => (
                        <div key={player.user_id}>
                            <p>{player.username}</p>
                            <p>Elo: {player.elo}</p>
                        </div>
                    ))}
                    <h3>Bots: {recommendations.bots.length}</h3>
                    {recommendations.bots.map((player) => (
                        <div key={player.user_id}>
                            <p>{player.username}</p>
                            <p>Elo: {player.elo}</p>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
