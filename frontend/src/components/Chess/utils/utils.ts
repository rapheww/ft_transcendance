import { useEffect, useState } from "react";
import { useAuth } from "../../AuthProvider";
import { API } from "./api";
import { emptyStats, type StatsProfil } from "../../Account/Profil/Chart";

export const horizontalAxis: string[] = ["a", "b", "c", "d", "e", "f", "g", "h"];
export const verticalAxis: string[] = ["1", "2", "3", "4", "5", "6", "7", "8"];

export const names = {
    p: "pawn",
    n: "knight",
    b: "bishop",
    k: "king",
    q: "queen",
    r: "rook",
} as const;

export type Movements = {
  bg: string;
  tile: HTMLElement;
};

export interface LastPick {
  piece: HTMLElement;
  bg: string;
}

export interface PromoParams{
  target: {x: number, y: number} | undefined;
  x: number;
  y: number;
  chessboard: HTMLElement;
  active: HTMLElement | null
}

//get current tile color
export function getColor(back: HTMLElement): string | null {
  const color = back.style.backgroundColor;
  return color;
}

export function getTileElement(x: number, y: number): HTMLElement | null {
  const chessboard = document.getElementById("chessboard");
  if (!chessboard) return null;
  const flipped = chessboard.dataset.flipped === "true";
  const index = flipped ? y * 8 + (7 - x) : (7 - y) * 8 + x;
  return chessboard.children[index] as HTMLElement ?? null;
}

export function squareToPos(square: string) {
  if (square.length > 2) square = square.substring(1);
  const x = horizontalAxis.indexOf(square[0]);
  const y = verticalAxis.indexOf(square[1]);
  return { x, y };
}

export function resetPiece(piece: HTMLElement) {
  piece.style.position = "";
  piece.style.left = "";
  piece.style.top = "";
  piece.style.width = "";
  piece.style.height = "";
  piece.style.zIndex = "";
}

export function getStats(username: string, refresh?: boolean){
  const [stats, setStats] = useState<StatsProfil>(emptyStats);
    const { token } = useAuth();
  
    useEffect(() => {
      if (!username || username === 'unknown') return;
      (async () => {
        try {
          const response = await fetch(
            `${API}/stats/player/${username}`,
            {
              headers: { Authorization: `Bearer ${token}` },
            },
          );
          if (!response.ok) return;
          const infos = await response.json();
          setStats(infos);
        } catch (err) {
          console.error(err);
        }
      })();
    }, [username, refresh]);
  return stats
}