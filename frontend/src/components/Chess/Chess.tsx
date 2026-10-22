import Header from "../Navbar/Header";
import { useEffect, useMemo, useRef, useState } from "react";
import Chessboard from "./board/Chessboard";
import { Flag } from "lucide-react";
import Timer from "./Timer";
import { useParams } from "react-router-dom";
import ProfilePreview from "./preview/ProfilePreview";
import { useAuth } from "../AuthProvider";
import { useGame } from "./utils/useGame";
import type { Moves } from "./utils/game";

export default function Chess() {
  const [showMoves, setShowMoves] = useState<boolean>(true);
  const [showChat, setShowChat] = useState<boolean>(false);
  const [wBonus, setWBonus] = useState<boolean>(false);
  const [bBonus, setBBonus] = useState<boolean>(false);
  const [open, setOpen] = useState<boolean>(false);
  const [username, setUsername] = useState<string>("");
  const [message, setMessage] = useState<string>("");
  const movesListRef = useRef<HTMLDivElement>(null);
  const { timer, bonus, gameId } = useParams<{
    timer: string;
    bonus: string;
    gameId: string;
  }>();

  const { user, token } = useAuth();

  // Les paramètres de l'URL sont du texte : n'accepter que les durées prévues pour la partie.
  const chrono =
    timer === "1" || timer === "5" || timer === "10" ? Number(timer) : 0;
  const add = bonus === "0" || bonus === "5" ? Number(bonus) : 0;
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
    opponentConnected,
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
  } = useGame(id, token);

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

      <main className="min-h-[calc(100dvh-72px)] flex items-center justify-center px-2 md:px-4">
        <div className="flex flex-col md:flex-row lg:grid lg:grid-cols-[1fr_auto_1fr] items-center md:items-stretch lg:items-center gap-2 md:gap-3 justify-center w-full max-w-470 md:h-[calc(100dvh-72px-2rem)]">
          {/* Le centre contient le plateau et les chronomètres. Le panneau latéral montre les coups ou le chat. */}
          <div className="flex flex-col h-full w-full justify-center items-center order-1 lg:col-start-2 lg:row-start-1 lg:-translate-x-20 gap-2 md:w-auto md:h-full md:max-w-[calc(100%-clamp(240px,26vw,420px)-0.75rem)] md:shrink lg:h-auto lg:max-w-none">
            <div className="flex flex-row justify-between items-center w-full h-10 shrink-0 p-3 rounded-sm bg-mist-400/10">
              <p
                onClick={() => {
                  setOpen(true);
                  setUsername(opponentName);
                }}
                className="text-lg font-semibold hover:text-gray-300 rounded-sm p-1 cursor-pointer flex items-center gap-2"
              >
                <>
                  {opponentName}
                  <span
                    aria-hidden
                    title={
                      opponentConnected
                        ? "Opponent connected"
                        : "Opponent disconnected"
                    }
                    className={`w-2 h-2 rounded-full inline-block ${opponentConnected ? "bg-green-400" : "bg-gray-500"}`}
                  />
                </>
              </p>

              {/* Afficher l'état de la connexion, y compris pour les outils d'assistance. */}
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
                  (playerColor === "black" ? wTurn : bTurn)
                    ? "bg-white/90 rounded-sm p-1 pl-2 pr-2 text-mist-700"
                    : ""
                }`}
              >
                <Timer
                  time={chrono * 60}
                  turn={playerColor === "black" ? wTurn : bTurn}
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
                className="w-full text-center text-[11px] text-gray-300"
              >
                {socketError}
              </p>
            )}

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
                canPlay={canPlay}
                sendSocketMove={sendSocketMove}
              />
            </div>

            <div className="flex flex-row justify-between items-center w-full h-10 shrink-0 p-3 rounded-sm bg-mist-400/10">
              <p
                onClick={() => {
                  setOpen(true);
                  setUsername(playerName || "You");
                }}
                className="text-lg font-semibold hover:text-gray-300 rounded-sm p-1 cursor-pointer"
              >
                {playerName || user || "You"} ({playerColor})
              </p>

              <div
                id="timer-2"
                className={`${
                  (playerColor === "black" ? bTurn : wTurn)
                    ? "bg-white/90 rounded-sm p-1 pl-2 pr-2 text-mist-700"
                    : ""
                }`}
              >
                <Timer
                  time={chrono * 60}
                  turn={playerColor === "black" ? bTurn : wTurn}
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
            {/* Ces boutons permettent de passer de la liste des coups au chat. */}
            <div className="w-full h-[5%] min-h-10 flex items-center justify-center rounded-t-md bg-mist-900/70">
              <div
                className={`flex justify-center items-center uppercase w-1/2 h-full ${showMoves ? "bg-gray-400/40" : "hover:bg-gray-400/20"} rounded-tl-md cursor-pointer`}
                onClick={() => {
                  setShowChat(false);
                  setShowMoves(true);
                }}
              >
                <p>movements</p>
              </div>
              <div
                className={`flex justify-center items-center uppercase w-1/2 h-full ${showChat ? "bg-gray-400/40" : "hover:bg-gray-400/20"} rounded-tr-md cursor-pointer`}
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

                    {/* Cette position correspond au plateau juste après le coup. */}
                    <div
                      id={`mov-white-${i}`}
                      data-fen={mov[0]?.fen}
                      onClick={() => mov[0] && setViewIndex(i * 2)}
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
                      onClick={() => mov[1] && setViewIndex(i * 2 + 1)}
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
              <div className="w-full h-[92%] flex flex-col gap-1 items-center">
                {chat.map((c) => (
                  <div key={c.id} className={`flex flex-row gap-2 w-full p-2 ${c.username != user ? 'bg-gray-700' : ''}`}>
                    <p>{c.username}: </p>
                    <p>{c.message}</p>
                  </div>
                ))}
              </div>

              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  setMessage("");
                  if(user){
                    sendChat({ type: "chat", message: message, username: user});
                  }
                }}
                className="h-[8%] flex flex-col items-center w-full"
              >
                <input
                  type="text"
                  placeholder="type your message here"
                  className="input input-primary outline-0 w-full h-full min-h-10 border-black border-t-2 rounded-b-md rounded-t-none"
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
