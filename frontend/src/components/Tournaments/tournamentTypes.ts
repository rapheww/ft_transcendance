export interface TournamentParticipant {
    id: number;
    username: string;
    eliminated: boolean;
}

export type TournamentMatchStatus = "scheduled" | "active" | "finished" | "bye";

export interface TournamentMatch {
    round: number;
    slot: number;
    player1_id: number | null;
    player2_id: number | null;
    game_id: number | null;
    winner_id: number | null;
    is_bye: boolean;
    status: TournamentMatchStatus;
}

export interface Tournament {
    id: number;
    status: string;
    organizer_type: string;
    creator_id: number | null;
    winner_id: number | null;
    created_at: string;
    registration_deadline: string;
    next_round_at: string | null;
    current_round: number;
    participant_count: number;
    participants: string[];
    participant_details: TournamentParticipant[];
    matches: TournamentMatch[];
    my_game_id: number | null;
}
