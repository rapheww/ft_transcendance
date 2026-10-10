import Header from "../Navbar/Header";
import { useEffect, useMemo, useRef, useState } from "react";
import Chessboard from "./Chessboard";
import { Flag } from "lucide-react";
import Timer from "./Timer";
import { useParams } from "react-router-dom";
import { useAuth } from "../AuthProvider";
import ProfilePreview from "./ProfilePreview";

export type Moves = {
  move: string;
  fen: string;
};

interface GameInfo {
  id: number;
  white_player_id: number | null;
  black_player_id: number | null;
  status: string;
  current_fen: string;
  fen?: string;
  result: string | null;
}

function getUserIdFromToken(token: string): number | null {
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;

    const base64 = payload
      .replace(/-/g, "+")
      .replace(/_/g, "/");

    const decoded = JSON.parse(
      atob(base64.padEnd(Math.ceil(base64.length / 4) * 4, "="))
    );

    const id = Number(decoded.sub);
    return Number.isInteger(id) && id > 0 ? id : null;
  } catch {
    return null;
  }
}

export default function Chess() {
  const [showMoves, setShowMoves] = useState(true);
  const [showChat, setShowChat] = useState(false);
  const [moves, setMoves] = useState<Moves[]>([]);
  const [wBonus, setWBonus] = useState(false);
  const [bBonus, setBBonus] = useState(false);
  const [open, setOpen] = useState(false);
  const [username, setUsername] = useState("");
  const [viewIndex, setViewIndex] = useState(-1);
  const socketRef = useRef<WebSocket | null>(null);
  const socketFenRef = useRef<string>("");

  const movesListRef = useRef<HTMLDivElement>(null);

  const { timer, bonus, gameId } = useParams<{
    timer: string;
    bonus: string;
    gameId: string;
  }>();

  const { user, token } = useAuth();

  const chrono =
    timer === "5" || timer === "10" ? Number(timer) : 0;

  const add =
    bonus === "0" || bonus === "5" ? Number(bonus) : 0;

  const id = Number(gameId);

  const [game, setGame] = useState<GameInfo | null>(null);
  const [fen, setFen] = useState("");
  const [gameOver, setGameOver] = useState(false);
  const [result, setResult] = useState("0-0");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");

  const userId = token ? getUserIdFromToken(token) : null;

  const playerColor: string =
    game && userId !== null
      ? game.white_player_id === userId
        ? "white"
        : game.black_player_id === userId
          ? "black"
          : ""
      : "";

  const opponentId =
    playerColor === "white"
      ? game?.black_player_id
      : playerColor === "black"
        ? game?.white_player_id
        : null;

  const opponentName = opponentId
    ? `Player ${opponentId}`
    : "Waiting for opponent";

  const wTurn = !gameOver && moves.length % 2 === 0;
  const bTurn = !gameOver && moves.length % 2 === 1;

  // Load the game already assigned by matchmaking.
  // Do not create or join another game here.
  useEffect(() => {
    if (!token || !Number.isInteger(id) || id <= 0) return;

    const ws = new WebSocket(
      `ws://127.0.0.1:8000/ws/games/${id}?token=${encodeURIComponent(token)}`
    );

    socketRef.current = ws;

    ws.onmessage = (event) => {
      let data: any;

      try {
        data = JSON.parse(event.data);
      } catch {
        return;
      }

      if (data.type === "game_connected") {
        if (data.fen) {
          socketFenRef.current = data.fen;
          setFen(data.fen);
        }

        if (data.status === "finished") {
          setGameOver(true);
          setResult(data.result ?? "0-0");
        }

        return;
      }

      if (data.type === "game_state") {
        if (data.fen) {
          socketFenRef.current = data.fen;
          setFen(data.fen);
        }

        if (data.status === "finished") {
          setGameOver(true);
          setResult(data.result ?? "0-0");
        }

        return;
      }

      if (data.type === "move") {
        if (data.fen) {
          socketFenRef.current = data.fen;
        }

        if (data.san && data.fen) {
          setMoves((previous) => {
            // Prevent duplicate history entries.
            const last = previous[previous.length - 1];

            if (last?.fen === data.fen) {
              return previous;
            }

            return [
              ...previous,
              { move: data.san, fen: data.fen },
            ];
          });
        }

        return;
      }

      if (data.type === "game_over") {
        setGameOver(true);
        setResult(data.result ?? "0-0");
      }
    };

    ws.onerror = () => {
      console.error("Game WebSocket connection failed.");
    };

    ws.onclose = () => {
      if (socketRef.current === ws) {
        socketRef.current = null;
      }
    };

    return () => {
      ws.close();
      if (socketRef.current === ws) {
        socketRef.current = null;
      }
    };
  }, [id, token]);

  const movePairs = useMemo(() => {
    const pairs: (Moves | null)[][] = [];

    for (let i = 0; i < moves.length; i += 2) {
      pairs.push([moves[i], moves[i + 1] ?? null]);
    }

    return pairs;
  }, [moves]);

  useEffect(() => {
    if (movesListRef.current) {
      movesListRef.current.scrollTop =
        movesListRef.current.scrollHeight;
    }
  }, [moves]);

  useEffect(() => {
    if (!open) return;

    function escHandler(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        setOpen(false);
      }
    }

    document.addEventListener("keydown", escHandler);

    return () => {
      document.removeEventListener("keydown", escHandler);
    };
  }, [open]);

  async function sendResign() {
    if (!token || !game || playerColor === "") return;

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/games/${id}/resign`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        console.error("Resign rejected:", await response.text());
        return;
      }

      const data: GameInfo = await response.json();

      setGame(data);
      setResult(data.result ?? "0-0");
      setGameOver(true);
    } catch (error) {
      console.error("Error resigning:", error);
    }
  }

  function showPrevMove(moveId: string) {
    const element = document.getElementById(moveId);

    if (!element?.dataset.fen) return;

    setFen(element.dataset.fen);
  }

  useEffect(() => {
    setViewIndex(moves.length - 1);
  }, [moves.length]);

  useEffect(() => {
    function arrowHandler(e: KeyboardEvent) {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") {
        return;
      }

      if (e.target instanceof HTMLInputElement) return;
      if (moves.length === 0) return;

      e.preventDefault();

      setViewIndex((index) =>
        e.key === "ArrowLeft"
          ? Math.max(index - 1, 0)
          : Math.min(index + 1, moves.length - 1)
      );
    }

    document.addEventListener("keydown", arrowHandler);

    return () => {
      document.removeEventListener("keydown", arrowHandler);
    };
  }, [moves.length]);

  useEffect(() => {
    if (viewIndex < 0 || !moves[viewIndex]) return;

    setFen(moves[viewIndex].fen);
  }, [viewIndex, moves]);

  if (loading) {
    return (
      <div className="min-h-screen">
        <Header />
        <p className="text-center mt-10">Loading game...</p>
      </div>
    );
  }

  if (loadError || !game || !fen) {
    return (
      <div className="min-h-screen">
        <Header />
        <div className="p-6 text-center">
          <p>{loadError || "Game data is unavailable."}</p>
        </div>
      </div>
    );
  }

  if (!playerColor) {
    return (
      <div className="min-h-screen">
        <Header />
        <p className="p-6 text-center">
          Your account is not assigned to this game.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full min-h-screen">
      <Header />

      <main className="min-h-[calc(100dvh-72px)] flex items-center justify-center px-2 md:px-4">
        <div className="flex flex-col md:flex-row lg:grid lg:grid-cols-[1fr_auto_1fr] items-center md:items-stretch lg:items-center gap-2 md:gap-3 justify-center w-full max-w-470 md:h-[calc(100dvh-72px-2rem)]">
          <div className="flex flex-col h-full w-full justify-center items-center order-1 lg:col-start-2 lg:row-start-1 lg:-translate-x-20 gap-2 md:w-auto md:h-full md:max-w-[calc(100%-clamp(240px,26vw,420px)-0.75rem)] md:shrink lg:h-auto lg:max-w-none">
            <div className="flex flex-row justify-between items-center w-full h-10 shrink-0 p-3 rounded-sm bg-mist-400/10">
              <p
                onClick={() => {
                  setOpen(true);
                  setUsername(opponentName);
                }}
                className="text-lg font-semibold hover:text-gray-300 rounded-sm p-1 cursor-pointer"
              >
                {playerColor === "white"
                  ? opponentName
                  : user || "You"}
              </p>

              <div
                id="timer-1"
                className={`${
                  bTurn
                    ? "bg-white/90 rounded-sm p-1 pl-2 pr-2 text-mist-700"
                    : ""
                }`}
              >
                <Timer
                  time={chrono * 60}
                  turn={bTurn}
                  bonus={add}
                  toAdd={bBonus}
                  setGameOver={setGameOver}
                />
              </div>
            </div>

            <div className="w-full aspect-square max-h-[65dvh] md:max-h-none md:h-auto md:w-[calc(100dvh-72px-8rem)] lg:h-auto lg:w-[min(calc(100dvh-72px-8rem),calc(100vw-2*clamp(240px,26vw,420px)-14.5rem))] flex items-center justify-center @container-size">
              <Chessboard
                setMoves={setMoves}
                setBBonus={setBBonus}
                setWBonus={setWBonus}
                setGameOver={setGameOver}
                setResult={setResult}
                gameId={id}
                fenInit={fen}
                gameOver={gameOver}
                result={result}
                playerColor={playerColor}
                sendSocketMessage={() => false}
              />
            </div>

            <div className="flex flex-row justify-between items-center w-full h-10 shrink-0 p-3 rounded-sm bg-mist-400/10">
              <p
                onClick={() => {
                  setOpen(true);
                  setUsername(user || "You");
                }}
                className="text-lg font-semibold hover:text-gray-300 rounded-sm p-1 cursor-pointer"
              >
                {user || "You"}
                {" "}
                ({playerColor})
              </p>

              <div
                id="timer-2"
                className={`${
                  wTurn
                    ? "bg-white/90 rounded-sm p-1 pl-2 pr-2 text-mist-700"
                    : ""
                }`}
              >
                <Timer
                  time={chrono * 60}
                  turn={wTurn}
                  bonus={add}
                  toAdd={wBonus}
                  setGameOver={setGameOver}
                />
              </div>
            </div>
          </div>

          <div
            id="mov-resume"
            className="flex order-2 shrink-0 w-full md:h-full md:max-h-[80%] md:w-[clamp(240px,26vw,520px)] lg:col-start-3 lg:row-start-1 lg:justify-self-start rounded-md shadow-[0_0_6px_#000000] bg-mist-800 items-center justify-center flex-col"
          >
            <div className="w-full h-[5%] min-h-10 flex items-center justify-center rounded-t-md p-2 bg-mist-900/70">
              <p
                onClick={() => {
                  setShowChat(false);
                  setShowMoves(true);
                }}
                className="text-center uppercase w-1/2 hover:bg-gray-400/20 rounded-md cursor-pointer"
              >
                movements
              </p>

              <p
                onClick={() => {
                  setShowMoves(false);
                  setShowChat(true);
                }}
                className="text-center uppercase w-1/2 hover:bg-gray-400/20 rounded-md cursor-pointer"
              >
                CHAT
              </p>
            </div>

            <div
              id="moves"
              className={`moves-list ${
                showMoves ? "flex" : "hidden"
              } flex-col w-full h-[95%] max-h-[95%]`}
            >
              <div
                ref={movesListRef}
                className="w-full h-[90%] flex flex-col overflow-y-scroll scroll-smooth"
              >
                {movePairs.map((mov, i) => (
                  <div
                    key={i}
                    className="flex flex-row w-full justify-center text-justify h-8 shrink-0"
                  >
                    <div className="flex justify-center w-[16%] bg-mist-700 h-auto">
                      {i + 1}
                    </div>

                    <div
                      id={`mov-white-${i}`}
                      data-fen={mov[0]?.fen}
                      onClick={() => showPrevMove(`mov-white-${i}`)}
                      className={`flex hover:bg-mist-500 cursor-pointer w-[42%] h-auto pl-2 ${
                        viewIndex === i * 2
                          ? "bg-white text-black"
                          : "bg-mist-800"
                      }`}
                    >
                      {mov[0]?.move}
                    </div>

                    <div
                      id={`mov-black-${i}`}
                      data-fen={mov[1]?.fen}
                      onClick={() => showPrevMove(`mov-black-${i}`)}
                      className={`flex w-[42%] hover:bg-mist-500 cursor-pointer h-auto pl-2 ${
                        viewIndex === i * 2 + 1
                          ? "bg-white text-black"
                          : "bg-mist-800"
                      }`}
                    >
                      {mov[1]?.move ?? ""}
                    </div>
                  </div>
                ))}
              </div>

              <div className="h-[10%] w-full flex flex-row justify-center items-center bg-mist-900/70 gap-3">
                <div className="flex justify-center items-center w-[15%] h-[60%] bg-mist-700/60 rounded-sm hover:bg-red-600/70 hover:scale-110 duration-300">
                  X
                </div>

                <button
                  type="button"
                  onClick={sendResign}
                  className="flex justify-center items-center w-[15%] h-[60%] bg-mist-700/60 rounded-sm hover:bg-red-600/50 hover:scale-110 duration-300"
                >
                  <Flag />
                </button>
              </div>
            </div>

            <div
              id="chat"
              className={`moves-list ${
                showChat ? "flex" : "hidden"
              } flex-col w-full h-[95%] max-h-[95%] overflow-y-scroll scroll-smooth`}
            >
              <div className="w-full h-[92%] flex justify-center items-center">
                <p>MESSAGE HERE</p>
              </div>

              <input
                type="text"
                placeholder="type your message here"
                className="input input-primary w-full h-[8%] min-h-10 border-black border-t-2 rounded-b-md rounded-t-none"
              />
            </div>
          </div>
        </div>

        <ProfilePreview
          onClose={() => setOpen(false)}
          open={open}
          username={username}
        />
      </main>
    </div>
  );
}
