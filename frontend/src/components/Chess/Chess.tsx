import Header from "../Navbar/Header";
import { useEffect, useMemo, useRef, useState } from "react";
import Chessboard from "./board/Chessboard";
import { Check, Flag, Undo2, X } from "lucide-react";
import Timer from "./Timer";
import { useNavigate, useParams } from "react-router-dom";
import ProfilePreview from "./preview/ProfilePreview";
import { useAuth } from "../AuthProvider";
import { useGame } from "./utils/useGame";
import type { Moves } from "./utils/game";
import { getStats } from "./utils/utils";

export default function Chess() {
  const [showMoves, setShowMoves] = useState<boolean>(true);
  const [showChat, setShowChat] = useState<boolean>(false);
  const [open, setOpen] = useState<boolean>(false);
  const [username, setUsername] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const movesListRef = useRef<HTMLDivElement>(null);
  const chatRef = useRef<HTMLDivElement>(null);
  const { gameId } = useParams<{
    gameId: string;
  }>();

  const navigate = useNavigate();
  const { user, token, profil } = useAuth();

  const id = Number(gameId);

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
    playerColor,
    playerName,
    opponentName,
    wTurn,
    bTurn,
    canPlay,
    sendSocketMove,
    sendChat,
    sendResign,
    chat,
    drawOffer,
    sendDraw,
  } = useGame(id, token);

  const opponentIsBot =
    playerColor === "white"
      ? game?.black_player_is_bot ?? false
      : game?.white_player_is_bot ?? false;
  const opponentElo = getStats(opponentName).elo;
  const playerElo = getStats(profil.username).elo;

  const movePairs = useMemo(() => {
    // Afficher les coups blancs et noirs côte à côte dans la liste des coups.
    const pairs: (Moves | null)[][] = [];

    for (let i = 0; i < moves.length; i += 2) {
      pairs.push([moves[i], moves[i + 1] ?? null]);
    }

    return pairs;
  }, [moves]);

  useEffect(() => {
    // Faire défiler la liste jusqu'aux nouveaux coups reçus sans demander au joueur de le faire.
    if (movesListRef.current) {
      movesListRef.current.scrollTop = movesListRef.current.scrollHeight;
    }
  }, [moves]);

  useEffect(() => {
    // Faire défiler la liste jusqu'aux nouveaux coups reçus sans demander au joueur de le faire.
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight;
    }
  }, [chat]);

  useEffect(() => {
    if (!open) return;

    // La touche Échap ferme l'aperçu du profil. Écouter cette touche seulement pendant son ouverture.
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

  if (loading) {
    // Afficher le chargement, l'erreur ou le refus d'accès avant les commandes de la partie.
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

      <main className="[--hdr:72px] [--panel:clamp(240px,26vw,420px)] [--board:min(calc(100vw-1rem),calc(100dvh-var(--hdr)-7rem))] md:[--board:max(18rem,min(calc(100vw-var(--panel)-3rem),calc(100dvh-var(--hdr)-8rem)))] min-h-[calc(100dvh-var(--hdr))] flex items-center justify-center p-2 md:p-4">
        <div className="flex flex-col md:flex-row items-center justify-center gap-2 md:gap-3">
          {/* Le centre contient le plateau et les chronomètres. Le panneau latéral montre les coups ou le chat. */}
          <div className="relative flex flex-col shrink-0 w-(--board) justify-center items-center order-1 gap-2">
            <div className="flex flex-row justify-between items-center gap-2 w-full h-10 shrink-0 px-2 sm:px-3 rounded-sm bg-black/20 backdrop-blur-xs ">
              <p
                onClick={() => {
                  setOpen(true);
                  setUsername(opponentName);
                }}
                className="min-w-0 overflow-hidden whitespace-nowrap text-sm sm:text-lg font-semibold hover:text-gray-300 rounded-sm p-1 cursor-pointer flex items-center gap-2"
              >
                <>
                  {opponentName} ({opponentElo})
                </>
              </p>

              {/* Afficher l'état de la connexion, y compris pour les outils d'assistance. */}
              <span
                role="status"
                aria-live="polite"
                title={socketError || undefined}
                className={`shrink-0 text-[10px] sm:text-xs ${
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
                className={`shrink-0 ${
                  (playerColor === "black" ? wTurn : bTurn)
                    ? "bg-white/90 rounded-sm p-1 pl-2 pr-2 text-mist-700"
                    : ""
                }`}
              >
                <Timer
                  time={
                    (playerColor === "black"
                      ? game.white_time_remaining
                      : game.black_time_remaining) ?? null
                  }
                  turn={playerColor === "black" ? wTurn : bTurn}
                  lastMoveAt={game.last_move_at}
                  setGameOver={setGameOver}
                />
              </div>
            </div>

            {socketError && (
              <p
                role="status"
                aria-live="polite"
                className="absolute top-14 left-1/2 z-30 max-w-[90%] -translate-x-1/2 truncate rounded bg-black/70 px-2 py-1 text-[11px] text-gray-200 pointer-events-none"
              >
                {socketError}
              </p>
            )}

            <div className="w-(--board) h-(--board) flex items-center justify-center @container-size">
              <Chessboard
                setMoves={setMoves}
                setGameOver={setGameOver}
                setResult={setResult}
                gameId={id}
                fenInit={fen}
                gameOver={gameOver}
                result={result}
                playerColor={playerColor}
                canPlay={canPlay}
                sendSocketMove={sendSocketMove}
                opponentName={opponentName}
                opponentType={game.opponent_type}
                opponentIsBot={opponentIsBot}
              />
            </div>

            <div className="flex flex-row justify-between items-center gap-2 w-full h-10 shrink-0 px-2 sm:px-3 rounded-sm bg-black/20 backdrop-blur-xs ">
              <p
                onClick={() => {
                  setOpen(true);
                  setUsername(playerName || "You");
                }}
                className="min-w-0 truncate text-sm sm:text-lg font-semibold hover:text-gray-300 rounded-sm p-1 cursor-pointer"
              >
                {playerName || user || "You"} ({playerElo})
              </p>

              <div
                id="timer-2"
                className={`shrink-0 ${
                  (playerColor === "black" ? bTurn : wTurn)
                    ? "bg-white/90 rounded-sm p-1 pl-2 pr-2 text-mist-700"
                    : ""
                }`}
              >
                <Timer
                  time={
                    (playerColor === "black"
                      ? game.black_time_remaining
                      : game.white_time_remaining) ?? null
                  }
                  turn={playerColor === "black" ? bTurn : wTurn}
                  lastMoveAt={game.last_move_at}
                  setGameOver={setGameOver}
                />
              </div>
            </div>
          </div>

          <div
            id="mov-resume"
            className="flex order-2 shrink-0 overflow-hidden h-72 w-(--board) md:h-[calc(var(--board)+6rem)] md:w-(--panel) rounded-md shadow-[0_0_6px_#000000] bg-black/20 backdrop-blur-xs items-center justify-center flex-col"
          >
            {/* Ces boutons permettent de passer de la liste des coups au chat. */}
            <div className="w-full h-10 shrink-0 flex items-center justify-center rounded-t-md border-b border-white/30">
              <div
                className={`flex justify-center items-center uppercase w-1/2 h-full ${showMoves ? "bg-white/15" : "hover:bg-white/15"} rounded-tl-md cursor-pointer`}
                onClick={() => {
                  setShowChat(false);
                  setShowMoves(true);
                }}
              >
                <p>movements</p>
              </div>
              <div
                className={`flex justify-center items-center uppercase w-1/2 h-full ${showChat ? "bg-white/15" : "hover:bg-white/15"} rounded-tr-md cursor-pointer`}
                onClick={() => {
                  setShowMoves(false);
                  setShowChat(true);
                }}
              >
                <p>CHAT</p>
              </div>
            </div>

            <div
              id="moves"
              className={`moves-list ${
                showMoves ? "flex" : "hidden"
              } flex-col w-full flex-1 min-h-0`}
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
              {drawOffer === "received" && (
                <div className="flex items-center justify-center gap-2 py-1 text-sm">
                  <span>Draw offered</span>
                </div>
              )}
              {drawOffer === "sent" && (
                <div className="flex items-center justify-center gap-2 py-1 text-sm">
                  <span className="text-lg">Draw sent</span>
                </div>
              )}
              {!gameOver && drawOffer === "none" ? (
                <div className="h-12 shrink-0 w-full flex flex-row justify-center items-center gap-3 border-t border-white/30">
                  <button
                    type="button"
                    disabled={drawOffer !== "none" || !canPlay}
                    onClick={() => sendDraw("draw_offer")}
                    className={`flex justify-center items-center w-12 h-8 border-2 ${game.can_claim_fifty_move || game.can_claim_threefold_repetition ? "bg-[#945003] hover:scale-110 duration-300" : "brightness-40"} border-white/20 rounded-sm`}
                  >
                    <p>1/2</p>
                  </button>

                  <button
                    type="button"
                    onClick={sendResign}
                    className="flex justify-center items-center w-12 h-8 border-2 border-white/20 rounded-sm hover:bg-red-600/40 hover:scale-110 duration-300"
                  >
                    <Flag />
                  </button>
                </div>
              ) : !gameOver && drawOffer === "received" && (
                <div className="h-12 shrink-0 w-full flex flex-row justify-center items-center gap-3 border-t border-white/30">
                  <p className="text-xs md:text-sm">Accept</p>
                  <button
                    type="button"
                    onClick={() => sendDraw("draw_accept")}
                    className="flex justify-center items-center w-12 h-8 border-2 border-white/20 rounded-sm bg-green-600/40 hover:scale-110 duration-300"
                  >
                    <Check />
                  </button>
                  <p className="text-xs md:text-sm">Decline</p>
                  <button
                    type="button"
                    onClick={() => sendDraw("draw_decline")}
                    className={`flex justify-center items-center w-12 h-8 border-2 bg-red-600/40 hover:scale-110 duration-300 border-white/20 rounded-sm`}
                  >
                    <X />
                  </button>
                </div>
              )}
              {gameOver && (
                <div className="h-12 shrink-0 w-full flex flex-row justify-center items-center gap-3 border-t border-white/30">
                  <button
                    type="button"
                    onClick={() =>
                      navigate(game.is_tournament ? "/tournaments" : "/")
                    }
                    className="flex justify-center items-center w-20 h-8 border-2 border-white/20 bg-white/10 rounded-sm hover:bg-red-600/40 hover:scale-110 duration-300"
                  >
                    <p className="mr-2 text-lg">Back</p>
                    <Undo2 size={20} />
                  </button>
                </div>
              )}
            </div>

            <div
              id="chat"
              className={`moves-list ${
                showChat ? "flex" : "hidden"
              } flex-col w-full flex-1 min-h-0 overflow-hidden`}
            >
              <div
                ref={chatRef}
                className="w-full flex-1 min-h-0 overflow-y-auto scroll-smooth flex flex-col items-center"
              >
                {chat.map((c) => (
                  <div
                    key={c.id}
                    className={`flex flex-row items-center gap-2 w-full p-2 ${c.username != user ? "bg-white/5" : ""} hover:bg-white/10`}
                  >
                    <p className="shrink-0 text-sm">{c.username}: </p>
                    <p className="min-w-0 wrap-break-word">{c.message}</p>
                  </div>
                ))}
              </div>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  setMessage("");
                  if (user) {
                    sendChat({
                      type: "chat",
                      message: message,
                      username: user,
                    });
                  }
                }}
                className="shrink-0 flex flex-col items-center w-full"
              >
                <input
                  type="text"
                  placeholder="type your message here"
                  className="input outline-0 border bg-white/1 border-white/20 w-full h-11 rounded-b-md rounded-t-none"
                  onChange={(e) => setMessage(e.target.value)}
                  value={message}
                />
              </form>
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
