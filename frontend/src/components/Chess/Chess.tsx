import Header from "../Navbar/Header";
import { useEffect, useMemo, useRef, useState } from "react";
import Chessboard from "./Chessboard";
import { Chess as ChessEngine } from "chess.js";
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
  // Player IDs may be null while a human matchmaking game is still waiting for its opponent.
  id: number;
  white_player_id: number | null;
  black_player_id: number | null;
  status: string;
  current_fen: string;
  fen?: string;
  pgn: string;
  result: string | null;
}

interface GameSocketMessage {
  // `type` selects which optional fields below are meaningful for each server event.
  type: string;
  fen?: string;
  status?: string;
  result?: string | null;
  pgn?: string;
  san?: string;
  message?: unknown;
}

type SocketStatus =
  | "connecting"
  | "connected"
  | "reconnecting"
  | "disconnected"
  | "finished";

const MAX_RECONNECT_ATTEMPTS = 8;
const INITIAL_RECONNECT_DELAY_MS = 1000;
const MAX_RECONNECT_DELAY_MS = 10000;

interface SocketGameState {
  fen: string;
  status?: string;
  result?: string | null;
}

function getMoveHistory(pgn: string): Moves[] {
  // PGN restores the complete SAN/FEN timeline for the move list and replay controls.
  const board = new ChessEngine();
  board.loadPgn(pgn);
  return board.history({ verbose: true }).map((move) => ({
    move: move.san,
    fen: move.after,
  }));
}

function appendMove(history: Moves[], move: Moves): Moves[] {
  // A reconnect snapshot can overlap with moves received while that snapshot was loading.
  if (history.some((entry) => entry.fen === move.fen)) return history;
  return [...history, move];
}

function readSocketGameState(stateRef: {
  current: SocketGameState | null;
}): SocketGameState | null {
  return stateRef.current;
}

function getUserIdFromToken(token: string): number | null {
  // The token's subject identifies which player record belongs to the signed-in user.
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

export default function Chess() {
  // `moves` is the canonical ordered history; `viewIndex` selects a replay position within it.
  const [showMoves, setShowMoves] = useState(true);
  const [showChat, setShowChat] = useState(false);
  const [moves, setMoves] = useState<Moves[]>([]);
  const [wBonus, setWBonus] = useState(false);
  const [bBonus, setBBonus] = useState(false);
  const [open, setOpen] = useState(false);
  const [username, setUsername] = useState("");
  const [viewIndex, setViewIndex] = useState(-1);
  // Refs hold the active socket and latest protocol state without causing renders on every event.
  const socketRef = useRef<WebSocket | null>(null);
  const socketFenRef = useRef<string>("");
  const socketSnapshotReceivedRef = useRef(false);
  const socketGameStateRef = useRef<SocketGameState | null>(null);
  const gameOverRef = useRef(false);

  const movesListRef = useRef<HTMLDivElement>(null);
  const { timer, bonus, gameId } = useParams<{
    timer: string;
    bonus: string;
    gameId: string;
  }>();

  const { user, token } = useAuth();
  // Route values are strings, so whitelist supported time controls before using them in timers/API flows.
  const chrono = timer === "5" || timer === "10" ? Number(timer) : 0;
  const add = bonus === "0" || bonus === "5" ? Number(bonus) : 0;
  const id = Number(gameId);

  const [game, setGame] = useState<GameInfo | null>(null);
  const [fen, setFen] = useState("");
  const [gameOver, setGameOver] = useState(false);
  const [result, setResult] = useState("0-0");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [socketStatus, setSocketStatus] = useState<SocketStatus>("connecting");
  const [socketError, setSocketError] = useState("");

  // Async socket callbacks read this ref to avoid acting on a stale render's game-over value.
  useEffect(() => {
    gameOverRef.current = gameOver;
  }, [gameOver]);

  const userId = token ? getUserIdFromToken(token) : null;

  // Resolve the local side from the backend's player IDs; empty means this account is not in this game.
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

  // The move count advances one half-move at a time, alternating whose clock is active.
  const wTurn = !gameOver && moves.length % 2 === 0;
  const bTurn = !gameOver && moves.length % 2 === 1;

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    // Load the persisted game first so direct links and page refreshes restore the same match.
    async function loadGame() {
      setLoading(true);
      setLoadError("");
      setGame(null);
      setFen("");
      setMoves([]);
      setViewIndex(-1);
      setGameOver(false);
      setResult("0-0");
      // Reset socket-derived state as well as UI state when the route switches to another game.
      socketSnapshotReceivedRef.current = false;
      socketGameStateRef.current = null;
      gameOverRef.current = false;

      if (!token) {
        setLoadError("You must be signed in to load this game.");
        setLoading(false);
        return;
      }

      if (!Number.isInteger(id) || id <= 0) {
        setLoadError("The game ID is invalid.");
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`http://127.0.0.1:8000/api/games/${id}`, {
          headers: { Authorization: `Bearer ${token}` },
          signal: controller.signal,
        });

        if (!response.ok) {
          const detail = await response.text();
          throw new Error(
            `Could not load game (${response.status})${detail ? `: ${detail}` : ""}`,
          );
        }

        const data = (await response.json()) as GameInfo;
        if (
          !data.current_fen ||
          typeof data.pgn !== "string" ||
          !Number.isInteger(data.id)
        ) {
          throw new Error("The server returned invalid game data.");
        }

        if (cancelled) return;

        // The socket may connect before this request finishes; prefer its newer snapshot if available.
        const socketState = readSocketGameState(socketGameStateRef);
        setGame(
          socketState
            ? {
                ...data,
                current_fen: socketState.fen || data.current_fen,
                status: socketState.status ?? data.status,
                result:
                  socketState.result !== undefined
                    ? socketState.result
                    : data.result,
              }
            : data,
        );
        setFen(socketState?.fen || data.current_fen);
        if (!socketSnapshotReceivedRef.current) {
          const history = getMoveHistory(data.pgn);
          setMoves(history);
          setViewIndex(history.length - 1);
        }
        setGameOver((socketState?.status ?? data.status) === "finished");
        setResult(
          (socketState?.result !== undefined
            ? socketState.result
            : data.result) ?? "0-0",
        );
      } catch (error) {
        // Aborted requests belong to an unmounted/previous game and should not overwrite current UI.
        if (cancelled) return;
        setLoadError(
          error instanceof Error ? error.message : "Could not load game.",
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadGame();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [id, token]);

  // Subscribe to the assigned game only; creating/joining happens in the matchmaking flow.
  // Live socket events keep the board, move history, and finished state in sync for both players.
  useEffect(() => {
    if (!token || !Number.isInteger(id) || id <= 0) return;
    socketFenRef.current = "";
    let stopped = false;
    let terminal = gameOverRef.current;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
    let retryCount = 0;
    let snapshotReceived = false;
    let pendingMoves: Moves[] = [];

    // Encode the token because it is carried in the WebSocket query string, not an HTTP header.
    const socketUrl = `ws://127.0.0.1:8000/ws/games/${id}?token=${encodeURIComponent(token)}`;

    function receiveMove(data: GameSocketMessage) {
      if (typeof data.san !== "string" || typeof data.fen !== "string") return;
      const move = { move: data.san, fen: data.fen };

      // Buffer live moves until the initial PGN snapshot establishes the history they follow.
      if (!snapshotReceived) {
        pendingMoves.push(move);
        return;
      }

      setMoves((history) => appendMove(history, move));
    }

    function scheduleReconnect() {
      if (stopped || terminal) return;

      // Exponential backoff limits reconnect traffic while capping how long each retry waits.
      if (retryCount >= MAX_RECONNECT_ATTEMPTS) {
        setSocketStatus("disconnected");
        setSocketError(
          `Could not reconnect after ${MAX_RECONNECT_ATTEMPTS} attempts. Reload the page to try again.`,
        );
        return;
      }

      const delay = Math.min(
        INITIAL_RECONNECT_DELAY_MS * 2 ** retryCount,
        MAX_RECONNECT_DELAY_MS,
      );
      retryCount += 1;
      setSocketStatus("reconnecting");
      setSocketError(
        `Connection lost. Reconnecting (${retryCount}/${MAX_RECONNECT_ATTEMPTS})...`,
      );
      reconnectTimer = setTimeout(connect, delay);
    }

    function handleMessage(event: MessageEvent<string>) {
      let data: GameSocketMessage;

      try {
        data = JSON.parse(event.data) as GameSocketMessage;
      } catch {
        setSocketError("Received an invalid WebSocket message.");
        return;
      }

      if (data.type === "game_connected") {
        // Connection handshake includes a full snapshot, allowing initial load and reconnect recovery.
        retryCount = 0;
        socketGameStateRef.current = {
          fen: data.fen ?? "",
          status: data.status,
          result: data.result,
        };
        if (data.fen) {
          socketFenRef.current = data.fen;
          setFen(data.fen);
        }

        if (typeof data.pgn === "string") {
          try {
            // Use the server snapshot as the baseline, then append any non-overlapping buffered moves.
            const history = getMoveHistory(data.pgn);
            const syncedMoves = pendingMoves.reduce(appendMove, history);
            snapshotReceived = true;
            socketSnapshotReceivedRef.current = true;
            setMoves(syncedMoves);
            setViewIndex(syncedMoves.length - 1);
            pendingMoves = [];
            setSocketError("");
          } catch {
            snapshotReceived = true;
            socketSnapshotReceivedRef.current = true;
            setSocketError(
              "Could not restore move history from the game snapshot.",
            );
            const queuedMoves = pendingMoves;
            pendingMoves = [];
            setMoves((history) => queuedMoves.reduce(appendMove, history));
          }
        } else {
          setSocketError("The server snapshot did not include move history.");
        }

        if (data.status) {
          const status = data.status;
          setGame((current) =>
            current
              ? {
                  ...current,
                  current_fen: data.fen ?? current.current_fen,
                  status,
                  result: data.result ?? current.result,
                }
              : current,
          );
        }

        if (data.status === "finished") {
          terminal = true;
          gameOverRef.current = true;
          setSocketStatus("finished");
          setGameOver(true);
          setResult(data.result ?? "0-0");
        } else if (data.status === "active") {
          gameOverRef.current = false;
          setGameOver(false);
        }

        return;
      }

      if (data.type === "game_state") {
        // State-only broadcasts update live position/outcome without replacing the move history.
        const previousSocketState = socketGameStateRef.current;
        socketGameStateRef.current = {
          fen: data.fen ?? previousSocketState?.fen ?? "",
          status: data.status ?? previousSocketState?.status,
          result:
            data.result !== undefined
              ? data.result
              : previousSocketState?.result,
        };
        if (data.fen) {
          socketFenRef.current = data.fen;
          setFen(data.fen);
        }

        if (data.status) {
          const status = data.status;
          setGame((current) =>
            current
              ? {
                  ...current,
                  current_fen: data.fen ?? current.current_fen,
                  status,
                  result: data.result ?? current.result,
                }
              : current,
          );
        }

        if (data.status === "finished") {
          terminal = true;
          gameOverRef.current = true;
          setSocketStatus("finished");
          setGameOver(true);
          setResult(data.result ?? "0-0");
        } else if (data.status === "active") {
          gameOverRef.current = false;
          setGameOver(false);
        }

        return;
      }

      if (data.type === "move") {
        // Moves carry SAN for display and FEN for replay; the server has already accepted the move.
        if (data.fen) {
          socketFenRef.current = data.fen;
        }
        receiveMove(data);
        return;
      }

      if (data.type === "error") {
        setSocketError(String(data.message ?? "WebSocket server error."));
        return;
      }

      if (data.type === "game_over") {
        // Terminal events stop further reconnect attempts and immediately freeze both clocks.
        terminal = true;
        gameOverRef.current = true;
        socketGameStateRef.current = {
          fen: socketFenRef.current,
          status: "finished",
          result: data.result,
        };
        setSocketStatus("finished");
        setGameOver(true);
        setResult(data.result ?? "0-0");
        setGame((current) =>
          current
            ? { ...current, status: "finished", result: data.result ?? null }
            : current,
        );
      }
    }

    function connect() {
      if (stopped || terminal || gameOverRef.current) {
        if (gameOverRef.current) setSocketStatus("finished");
        return;
      }

      setSocketStatus(retryCount === 0 ? "connecting" : "reconnecting");
      let ws: WebSocket;
      try {
        ws = new WebSocket(socketUrl);
      } catch {
        scheduleReconnect();
        return;
      }

      socketRef.current = ws;
      ws.onopen = () => {
        if (stopped || socketRef.current !== ws) return;
        setSocketStatus("connected");
        setSocketError("");
      };
      ws.onmessage = handleMessage;
      ws.onerror = () => {
        setSocketError("WebSocket connection error.");
        ws.close();
      };
      ws.onclose = () => {
        // Ignore a close from a superseded socket; only the current connection schedules a retry.
        if (socketRef.current === ws) socketRef.current = null;
        scheduleReconnect();
      };
    }

    connect();

    return () => {
      // Detach handlers before closing so cleanup cannot trigger state updates or another retry.
      stopped = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      const ws = socketRef.current;
      socketRef.current = null;
      if (ws) {
        ws.onopen = null;
        ws.onmessage = null;
        ws.onerror = null;
        ws.onclose = null;
        ws.close();
      }
    };
  }, [id, token]);

  const movePairs = useMemo(() => {
    // Group consecutive plies into the white/black rows used by the move list.
    const pairs: (Moves | null)[][] = [];

    for (let i = 0; i < moves.length; i += 2) {
      pairs.push([moves[i], moves[i + 1] ?? null]);
    }

    return pairs;
  }, [moves]);

  useEffect(() => {
    // Keep newly received live moves visible without forcing the user to scroll manually.
    if (movesListRef.current) {
      movesListRef.current.scrollTop = movesListRef.current.scrollHeight;
    }
  }, [moves]);

  useEffect(() => {
    if (!open) return;

    // The profile preview behaves like a dialog; Escape closes it and the listener is scoped to its lifetime.
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
    // Resignation is persisted by the API; local state changes only after its response succeeds.
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
        },
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
    // Each move row stores the resulting FEN, so replay does not need another server request.
    const element = document.getElementById(moveId);

    if (!element?.dataset.fen) return;

    setFen(element.dataset.fen);
  }

  useEffect(() => {
    // New history (for example, after a live move or snapshot) returns replay to the latest position.
    setViewIndex(moves.length - 1);
  }, [moves.length]);

  useEffect(() => {
    // Allow keyboard replay navigation, but leave arrow keys available while typing in an input.
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
          : Math.min(index + 1, moves.length - 1),
      );
    }

    document.addEventListener("keydown", arrowHandler);

    return () => {
      document.removeEventListener("keydown", arrowHandler);
    };
  }, [moves.length]);

  useEffect(() => {
    // Keep the board on the selected historical position as the move list or arrow keys change it.
    if (viewIndex < 0 || !moves[viewIndex]) return;

    setFen(moves[viewIndex].fen);
  }, [viewIndex, moves]);

  if (loading) {
    // Render explicit loading, fetch-error, and access-denied states before mounting the game controls.
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
          {/* The center column owns the live board and clocks; the side panel contains history/chat. */}
          <div className="flex flex-col h-full w-full justify-center items-center order-1 lg:col-start-2 lg:row-start-1 lg:-translate-x-20 gap-2 md:w-auto md:h-full md:max-w-[calc(100%-clamp(240px,26vw,420px)-0.75rem)] md:shrink lg:h-auto lg:max-w-none">
            <div className="flex flex-row justify-between items-center w-full h-10 shrink-0 p-3 rounded-sm bg-mist-400/10">
              <p
                onClick={() => {
                  setOpen(true);
                  setUsername(opponentName);
                }}
                className="text-lg font-semibold hover:text-gray-300 rounded-sm p-1 cursor-pointer"
              >
                {playerColor === "white" ? opponentName : user || "You"}
              </p>

              {/* Expose connection state both visually and to assistive technology. */}
              <span
                role="status"
                aria-live="polite"
                title={socketError || undefined}
                className={`text-xs ${
                  socketStatus === "connected"
                    ? "text-green-400"
                    : socketStatus === "disconnected"
                      ? "text-red-400"
                      : "text-amber-300"
                }`}
              >
                {socketStatus === "connected"
                  ? "Live"
                  : socketStatus === "connecting"
                    ? "Connecting"
                    : socketStatus === "reconnecting"
                      ? "Reconnecting"
                      : socketStatus === "finished"
                        ? "Game finished"
                        : "Offline"}
              </span>

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

            {socketError && (
              <p
                role="status"
                aria-live="polite"
                className="w-full text-center text-xs text-red-400"
              >
                {socketError}
              </p>
            )}

            <div className="w-full aspect-square max-h-[65dvh] md:max-h-none md:h-auto md:w-[calc(100dvh-72px-8rem)] lg:h-auto lg:w-[min(calc(100dvh-72px-8rem),calc(100vw-2*clamp(240px,26vw,420px)-14.5rem))] flex items-center justify-center @container-size">
              <Chessboard
                setBBonus={setBBonus}
                setWBonus={setWBonus}
                setGameOver={setGameOver}
                setResult={setResult}
                gameId={id}
                fenInit={fen}
                gameOver={gameOver}
                result={result}
                playerColor={playerColor}
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
                {user || "You"} ({playerColor})
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
            {/* These controls switch between the move replay list and the chat panel. */}
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

                    {/* Each square's FEN is the position immediately after that half-move. */}
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
