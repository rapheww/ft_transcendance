export const API = "http://127.0.0.1:8000/api";

export async function postMove(move: string, gameId: number, token: string) {
  try {
    const response = await fetch(
      `${API}/games/${gameId}/move`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          move: move,
        }),
      },
    );
    if (!response.ok) return false;
    return response.json();
    
    return true;
  } catch {
    console.log("error makeMove");
    return false;
  }
}

export async function getResult(token: string, gameId: number) {
  try {
    const response = await fetch(`${API}/games/${gameId}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!response.ok) return null;
    return response.json();
  } catch {
    return;
  }
}
