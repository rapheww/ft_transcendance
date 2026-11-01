import { Chess as ChessEngine } from "chess.js";

export type Moves = {
  move: string;
  fen: string;
};

export interface GameInfo {
  // Les identifiants peuvent être absents tant qu'un joueur attend son adversaire.
  id: number;
  white_player_id: number | null;
  white_player_name?: string;
  white_player_is_bot?: boolean;
  black_player_id: number | null;
  black_player_name?: string | null;
  black_player_is_bot?: boolean;
  opponent_type?: string;
  ai_difficulty?: string | null;
  is_tournament?: boolean;
  status: string;
  current_fen: string;
  fen?: string;
  pgn: string;
  result: string | null;
  white_time_remaining?: number | null;
  black_time_remaining?: number | null;
  increment_seconds?: number;
  last_move_at?: string | null;
  can_claim_threefold_repetition: boolean,
  can_claim_fifty_move: boolean
}

export interface GameSocketMessage {
  // Le champ « type » indique le genre de message et les données qu'il contient.
  type: string;
  fen?: string;
  status?: string;
  result?: string | null;
  pgn?: string;
  san?: string;
  message?: unknown;
  user_id?: number;
  username?: string;
  id?: number;
  chat?: ChatMessage[];
  white_time_remaining?: number | null;
  black_time_remaining?: number | null;
  increment_seconds?: number;
  last_move_at?: string | null;
  spectator_count?: number;
  count?: number;
  can_claim_threefold_repetition: boolean,
  can_claim_fifty_move: boolean
}

export interface ChatMessage {
  id: number;
  user_id: number;
  username: string;
  message: string;
}

export type SocketStatus =
  | "connecting"
  | "connected"
  | "reconnecting"
  | "disconnected"
  | "finished";

export const MAX_RECONNECT_ATTEMPTS = 8;
export const INITIAL_RECONNECT_DELAY_MS = 1000;
export const MAX_RECONNECT_DELAY_MS = 10000;

export interface SocketGameState {
  fen: string;
  status?: string;
  result?: string | null;
  white_time_remaining?: number | null;
  black_time_remaining?: number | null;
  increment_seconds?: number;
  last_move_at?: string | null;
  can_claim_threefold_repetition: boolean,
  can_claim_fifty_move: boolean
}

export function getMoveHistory(pgn: string): Moves[] {
  // Lire les coups enregistrés pour remplir la liste et permettre de revoir la partie.
  const board = new ChessEngine();
  board.loadPgn(pgn);
  return board.history({ verbose: true }).map((move) => ({
    move: move.san,
    fen: move.after,
  }));
}

export function appendMove(history: Moves[], move: Moves): Moves[] {
  // Après une reconnexion, le serveur peut renvoyer un coup déjà reçu pendant le chargement.
  // On vérifie donc la position obtenue pour éviter d'ajouter ce coup deux fois.
  if (history.some((entry) => entry.fen === move.fen)) return history;
  return [...history, move];
}

export function readSocketGameState(stateRef: {
  current: SocketGameState | null;
}): SocketGameState | null {
  return stateRef.current;
}

export function getUserIdFromToken(token: string): number | null {
  // Le champ « sub » du jeton contient l'identifiant du compte connecté.
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;

    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");

    const decoded = JSON.parse(
      atob(base64.padEnd(Math.ceil(base64.length / 4) * 4, "=")),
    );

    const id = Number(decoded.sub);
    return Number.isInteger(id) && id > 0 ? id : null;
  } catch {
    return null;
  }
}