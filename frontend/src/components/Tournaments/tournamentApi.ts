import type { Tournament } from "./tournamentTypes";

const API_URL = "http://127.0.0.1:8000/api/tournaments";

async function request<T>(path: string, token: string, method = "GET"): Promise<T> {
    const response = await fetch(`${API_URL}${path}`, {
        method,
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        const body = await response.text();
        throw new Error(`HTTP ${response.status}: ${body}`);
    }

    return response.json() as Promise<T>;
}

export function listTournaments(token: string): Promise<Tournament[]> {
    return request<Tournament[]>("/", token);
}

export function getMyTournament(token: string): Promise<Tournament | null> {
    return request<Tournament | null>("/me", token);
}

export function getTournament(id: number, token: string): Promise<Tournament> {
    return request<Tournament>(`/${id}`, token);
}

export function createTournament(token: string): Promise<Tournament> {
    return request<Tournament>("/", token, "POST");
}

export function joinTournament(id: number, token: string): Promise<Tournament> {
    return request<Tournament>(`/${id}/register`, token, "POST");
}

export function startTournament(id: number, token: string): Promise<Tournament> {
    return request<Tournament>(`/${id}/start`, token, "POST");
}
