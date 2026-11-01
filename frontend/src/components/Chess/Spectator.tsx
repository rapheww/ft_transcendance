import { Eye, Users } from "lucide-react";
import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Header from "../Navbar/Header";
import { useAuth } from "../AuthProvider";
import Chessboard from "./board/Chessboard";
import { useGame } from "./utils/useGame";
import type { Moves } from "./utils/game";

export default function Spectator() {
  const { gameId } = useParams<{ gameId: string }>();
  const navigate = useNavigate();
  const { token } = useAuth();
  const id = Number(gameId);
  const [clockNow, setClockNow] = useState(0);
  const movesListRef = useRef<HTMLDivElement>(null);

  const {
    game,
    fen,
    moves,
    setMoves,
    viewIndex,
    setViewIndex,
    gameOver,
    setGameOver,
    result,
    setResult,
    loading,
    loadError,
    socketStatus,
    socketError,
    spectatorCount,
  } = useGame(id, token || null, true);

  const movePairs = useMemo(() => {
    const pairs: (Moves | null)[][] = [];
    for (let i = 0; i < moves.length; i += 2) {
      pairs.push([moves[i], moves[i + 1] ?? null]);
    }
    return pairs;
  }, [moves]);

  useEffect(() => {
    if (movesListRef.current) {
      movesListRef.current.scrollTop = movesListRef.current.scrollHeight;
    }
  }, [moves]);

  useEffect(() => {
    if (game?.status !== "active") return;
    const interval = window.setInterval(() => setClockNow(Date.now()), 250);
    return () => window.clearInterval(interval);
  }, [game?.status]);

  if (loading) {
    return (
      <div className="min-h-screen">
        <Header />
        <p className="mt-10 text-center">Loading game...</p>
      </div>
    );
  }

  if (loadError || !game || !fen) {
    return (
      <div className="min-h-screen">
        <Header />
        <p role="alert" className="p-6 text-center">
          {loadError || "Game data is unavailable."}
        </p>
      </div>
    );
  }

  const whiteName = game.white_player_name || "White";
  const blackName =
    game.black_player_name ||
    (game.opponent_type === "ai" ? "Computer" : "Black");
  const isLive = socketStatus === "connected" && !gameOver;
  const isWaiting = game.status === "waiting";
  const isBlackTurn = game.current_fen.split(" ")[1] === "b";
  const isWhiteTurn = game.current_fen.split(" ")[1] === "w";

  function formatClock(
    seconds: number | null | undefined,
    isTurn: boolean,
    status: string,
    lastMoveAt: string | null | undefined,
  ) {
    if (seconds === null || seconds === undefined) return "--:--";
    const lastMoveTimestamp = lastMoveAt
      ? Date.parse(lastMoveAt)
      : Number.NaN;
    const elapsed =
      status === "active" && isTurn && Number.isFinite(lastMoveTimestamp)
        ? Math.floor(
            ((clockNow || lastMoveTimestamp) - lastMoveTimestamp) / 1000,
          )
        : 0;
    const remaining = Math.max(0, seconds - elapsed);
    return `${Math.floor(remaining / 60)}:${String(remaining % 60).padStart(2, "0")}`;
  }

  return (
    <div className="min-h-screen w-full">
      <Header />
      <main className="mx-auto flex min-h-[calc(100dvh-72px)] w-full max-w-7xl flex-col items-center justify-center gap-4 px-3 py-5 md:px-6">
        <div className="flex w-full max-w-5xl flex-wrap items-center justify-between gap-3">
          <div>
            <p className="text-xs uppercase tracking-[0.25em] text-gray-400">
              Game {game.id}
            </p>
            <h1 className="text-2xl font-bold">Spectating match</h1>
            {!isWaiting && (
              <p className="mt-1 flex items-center gap-2 text-sm text-gray-300">
                <Users size={16} aria-hidden="true" />
                <span>{spectatorCount} watching</span>
              </p>
            )}
          </div>
          <div
            role="status"
            aria-live="polite"
            className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-semibold ${
              isLive
                ? "bg-red-500/15 text-red-300"
                : gameOver
                  ? "bg-green-600/20 text-gray-200"
                  : "bg-amber-400/15 text-amber-200"
            }`}
          >
            <Eye size={16} aria-hidden="true" />
            {isLive
              ? "LIVE"
              : gameOver
                ? `Finished · ${result}`
                : isWaiting
                  ? "Waiting for players"
                : socketStatus === "reconnecting"
                  ? "Reconnecting"
                  : socketStatus === "disconnected"
                    ? "Offline"
                    : "Connecting"}
          </div>
        </div>

        {socketError && !isWaiting && (
          <p role="status" className="w-full max-w-5xl text-sm text-amber-200">
            {socketError}
          </p>
        )}

        {isWaiting ? (
          <section className="w-full max-w-5xl rounded-xl bg-mist-800 p-8 text-center">
            <h2 className="text-xl font-semibold">This match hasn’t started</h2>
            <p className="mt-2 text-sm text-gray-300">
              Refresh this page after both players have joined to start watching.
            </p>
            <button
              type="button"
              onClick={() => window.location.reload()}
              className="btn mt-5 bg-mist-700 hover:bg-mist-600"
            >
              Refresh match
            </button>
            <button
              type="button"
              onClick={() => navigate("/")}
              className="ml-3 mt-5 text-sm text-gray-300 underline"
            >
              Leave
            </button>
          </section>
        ) : (
          <div className="flex w-full max-w-5xl flex-col items-center gap-4 lg:flex-row lg:items-stretch">
            <section className="flex w-full max-w-[min(100%,42rem)] flex-col gap-2">
              <div className="flex min-h-12 items-center justify-between rounded-md bg-black/20 backdrop-blur-xs px-4">
                <span className="min-w-0 truncate font-semibold">
                  {blackName}
                  <span className="ml-2 text-xs uppercase tracking-wider text-gray-400">
                    Black
                  </span>
                </span>
                <span
                  className={`rounded px-3 py-1 font-mono text-lg font-bold ${
                    isBlackTurn && !gameOver
                      ? "bg-white text-mist-900"
                      : ""
                  }`}
                >
                  {formatClock(
                    game.black_time_remaining,
                    isBlackTurn,
                    game.status,
                    game.last_move_at,
                  )}
                </span>
              </div>
              <div className="aspect-square w-full @container-size">
                <Chessboard
                  setMoves={setMoves}
                  setGameOver={setGameOver}
                  setResult={setResult}
                  gameId={id}
                  fenInit={fen}
                  gameOver={gameOver}
                  result={result}
                  playerColor="white"
                  canPlay={false}
                  sendSocketMove={() => false}
                  readOnly
                  opponentName={""}
                  opponentType={game.opponent_type}
                  opponentIsBot={false}
                />
              </div>
              <div className="flex min-h-12 items-center justify-between rounded-md bg-black/20 backdrop-blur-xs px-4">
                <span className="min-w-0 truncate font-semibold">
                  {whiteName}
                  <span className="ml-2 text-xs uppercase tracking-wider text-gray-400">
                    White
                  </span>
                </span>
                <span
                  className={`rounded px-3 py-1 font-mono text-lg font-bold ${
                    isWhiteTurn && !gameOver
                      ? "bg-white text-mist-900"
                      : ""
                  }`}
                >
                  {formatClock(
                    game.white_time_remaining,
                    isWhiteTurn,
                    game.status,
                    game.last_move_at,
                  )}
                </span>
              </div>
            </section>
            <div
            id="mov-resume"
            className="flex max-h-[min(70dvh,42rem)] min-h-64 w-full flex-col overflow-hidden rounded-md shadow-[0_0_6px_#000000] bg-black/20 backdrop-blur-xs lg:mt-14 lg:max-w-sm"
          >
            {/* Ces boutons permettent de passer de la liste des coups au chat. */}
            <div className="w-full h-10 shrink-0 flex items-center justify-center rounded-t-md border-b border-white/30">
              <div
                className={`flex justify-center items-center uppercase w-1/2 h-full "bg-white/15" rounded-tl-md cursor-pointer`}
              >
                <p>movements</p>
              </div>
            </div>

            <div
              id="moves"
              className={`moves-list flex flex-col w-full flex-1 min-h-0`}
            >
              <div
                ref={movesListRef}
                className="w-full flex-1 min-h-0 flex flex-col overflow-y-auto scroll-smooth"
              >
                {movePairs.map((mov, i) => (
                  <div
                    key={i}
                    className="flex flex-row w-full justify-center text-justify h-8 shrink-0"
                  >
                    <div className="flex justify-center w-[16%] bg-white/1 border-r border-white/20 h-auto">
                      {i + 1}
                    </div>

                    {/* Cette position correspond au plateau juste après le coup. */}
                    <div
                      id={`mov-white-${i}`}
                      data-fen={mov[0]?.fen}
                      onClick={() => mov[0] && setViewIndex(i * 2)}
                      className={`flex hover:bg-white/15 cursor-pointer w-[42%] h-auto pl-2 ${
                        viewIndex === i * 2 ? "bg-white/25" : ""
                      }`}
                    >
                      {mov[0]?.move}
                    </div>

                    <div
                      id={`mov-black-${i}`}
                      data-fen={mov[1]?.fen}
                      onClick={() => mov[1] && setViewIndex(i * 2 + 1)}
                      className={`flex w-[42%] hover:bg-white/15 cursor-pointer h-auto pl-2 ${
                        viewIndex === i * 2 + 1 ? "bg-white/25" : ""
                      }`}
                    >
                      {mov[1]?.move ?? ""}
                    </div>
                  </div>
                ))}
              </div>
              <div className="border-t border-white/10 px-4 py-3 text-xs text-gray-400">
                {viewIndex < moves.length - 1
                  ? "Reviewing a previous position"
                  : "Following the live position"}
              </div>
            </div>
          </div>
          </div>
        )}
      </main>
    </div>
  );
}
