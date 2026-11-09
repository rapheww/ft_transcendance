import { API } from "../Chess/utils/api";
import type { BotInfo, Tournament } from "./tournamentTypes";

const API_URL = `${API}/tournaments`;

// CHANGED: errors now carry the HTTP status and the backend's readable message
// (e.g. "Already registered for this tournament") instead of raw JSON.
export class TournamentApiError extends Error {
    status: number;
    constructor(status: number, message: string) {
        super(message);
        this.status = status;
    }
}

async function request<T>(path: string, token: string, method = "GET"): Promise<T> {
    const response = await fetch(`${API_URL}${path}`, {
        method,
        headers: {
            Authorization: `Bearer ${token}`,
        },
    });

    if (!response.ok) {
        const body = await response.text();
        let message = body || `HTTP ${response.status}`;
        try {
            const detail = JSON.parse(body).detail;
            if (typeof detail === "string") message = detail;
        } catch {
            // body was not JSON: keep the raw text
        }
        throw new TournamentApiError(response.status, message);
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

// ADDED (optional bots): the organizer fills the empty places with bots, just before Start
export function fillWithBots(id: number, token: string): Promise<Tournament> {
    return request<Tournament>(`/${id}/bots`, token, "POST");
}

// ADDED (optional bots): the bots of a tournament, for the "AI" labels
export function getTournamentBots(id: number, token: string): Promise<BotInfo[]> {
    return request<BotInfo[]>(`/${id}/bots`, token);
}