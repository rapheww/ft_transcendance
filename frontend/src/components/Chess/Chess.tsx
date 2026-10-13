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

export default function Chess() {
  const [showMoves, setShowMoves] = useState<boolean>(true);
  const [showChat, setShowChat] = useState<boolean>(false);
  const [moves, setMoves] = useState<Moves[]>([]);
  const [wBonus, setWBonus] = useState<boolean>(false);
  const [bBonus, setBBonus] = useState<boolean>(false);
  const [open, setOpen] = useState<boolean>(false);
  const [username, setUsername] = useState<string>("");
  const [viewIndex, setViewIndex] = useState<number>(-1);

  const movesListRef = useRef<HTMLDivElement>(null);
  const { timer, bonus } = useParams<{ timer: string; bonus: string }>();
  const add = bonus === "0" || bonus === "5" ? Number(bonus) : 0;
  const chrono = timer === "5" || timer === "10" ? Number(timer) : 0;

  const [id, setId] = useState<number>(0);
  const [fen, setFen] = useState<string>("");
  const [gameOver, setGameOver] = useState<boolean>(false);
  const [result, setResult] = useState<string>("0-0");

  const wTurn = !gameOver && moves.length % 2 === 0;
  const bTurn = !gameOver && moves.length % 2 === 1;

  const { user, token } = useAuth();
  //a delete
  const user1 = "Bob";

  //tmp function
  const gameCreated = useRef(false);

  useEffect(() => {
    // pas de token = pas encore connecté, ou déjà créé
    if (!token || gameCreated.current) return;
    gameCreated.current = true;

    async function createGame() {
      try {
        const create = await fetch("http://127.0.0.1:8000/api/games/", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            initial_time_seconds: chrono * 60,
            increment_seconds: bonus ? bonus : 0,
          }),
        });

        if (!create.ok) {
          gameCreated.current = false; // permet de réessayer
          return;
        }

        const infos = await create.json();
        setId(infos.id);
        setFen(infos.fen);

        const join = await fetch(
          `http://127.0.0.1:8000/api/games/${infos.id}/join`, // infos.id, pas id
          {
            method: "POST",
            headers: {
              Authorization: `Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzkxOTE5MDY3LCJ0eXBlIjoiYWNjZXNzIn0.N0A6j9E8oy1zvNb32I_MHfydAd7R1Y_n403DOM7qmJY`,
            },
          },
        );
        console.log(await join.json());
      } catch (err) {
        console.log(err);
        gameCreated.current = false;
      }
    }

    createGame();
  }, [token]);

  const movePairs = useMemo(() => {
    let tmp: (Moves | null)[][] = [];
    let j = 0;
    for (let i = 0; i < moves.length; i += 2) {
      tmp[j] = [];
      tmp[j].push(moves[i], moves[i + 1] ? moves[i + 1] : null);
      j++;
    }
    return tmp;
  }, [moves]);

  useEffect(() => {
    if (movesListRef.current) {
      movesListRef.current.scrollTop = movesListRef.current.scrollHeight; //defini la hauteur a scroll par la hauteur actuelle de l'element
    }
  }, [moves]);

  //close Profil preview with esc
  useEffect(() => {
    if (!open) return;

    function escHandler(e: globalThis.KeyboardEvent) {
      if (open && e.key === "Escape") {
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
      const resignState = await response.json();
      setResult(resignState.result);
      setGameOver(true);
    } catch {
      console.log("error resign");
    }
  }

  function showPrevMove(premove: string) {
    const thisFen = document.getElementById(premove);
    if (!thisFen || !thisFen.dataset.fen) return;
    setFen(thisFen.dataset.fen);
  }

  useEffect(() => {
    setViewIndex(moves.length - 1);
  }, [moves.length]);

  //handle arrow from the last move only atm
  useEffect(() => {
    function arrowHandler(e: globalThis.KeyboardEvent) {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") return;
      if (e.target instanceof HTMLInputElement) return;
      e.preventDefault();
      setViewIndex((i) =>
        e.key === "ArrowLeft"
          ? Math.max(i - 1, 0)
          : Math.min(i + 1, moves.length - 1),
      );
    }
    document.addEventListener("keydown", arrowHandler);
    return () => {
      document.removeEventListener("keydown", arrowHandler);
    };
  }, [moves.length]);

  useEffect(() => {
    if (!moves[viewIndex]) return;
    setFen(moves[viewIndex].fen);
  }, [viewIndex]);

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
                  if (user1) setUsername(user1);
                }}
                className="text-lg font-semibold hover:text-gray-300 rounded-sm p-1 cursor-pointer"
              >
                {user1}
              </p>
              <div
                id="timer-1"
                className={`${bTurn ? "bg-white/90   rounded-sm p-1 pl-2 pr-2 text-mist-700" : ""}`}
              >
                <Timer
                  time={chrono * 60}
                  turn={bTurn}
                  bonus={add}
                  toAdd={bBonus}
                  setGameOver={setGameOver}
                />
              </div>
              {/* time a changer en fonction du mode donc passage en props */}
            </div>
            <div className="w-full aspect-square max-h-[65dvh] md:max-h-none md:h-auto md:w-[calc(100dvh-72px-8rem)] lg:h-auto lg:w-[min(calc(100dvh-72px-8rem),calc(100vw-2*clamp(240px,26vw,420px)-14.5rem))] flex items-center justify-center @container-size">
              {id ? (
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
                />
              ) : (
                <p>Création de la partie...</p>
              )}
            </div>
            <div className="flex flex-row justify-between items-center w-full h-10 shrink-0 p-3 rounded-sm bg-mist-400/10">
              <p
                onClick={() => {
                  setOpen(true);
                  if (user) setUsername(user);
                }}
                className="text-lg font-semibold hover:text-gray-300 rounded-sm p-1 cursor-pointer"
              >
                {user}
              </p>
              <div
                id="timer-2"
                className={`${wTurn ? "bg-white/90 rounded-sm p-1 pl-2 pr-2 text-mist-700" : ""}`}
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
            className={`flex 
              order-2 
              shrink-0 
              w-full
              md:h-full
              md:max-h-[80%]
              md:w-[clamp(240px,26vw,520px)]
              lg:col-start-3
              lg:row-start-1
              lg:justify-self-start
              rounded-md
              shadow-[0_0_6px_#000000]
              bg-mist-800 
              items-center 
              justify-center 
              flex-col
              `}
          >
            <div
              className={`w-full h-[5%] min-h-10 flex items-center justify-center rounded-t-md p-2 bg-mist-900/70`}
            >
              <p
                onClick={() => {
                  setShowChat(false);
                  setShowMoves(true);
                }}
                className="text-center uppercase w-1/2 hover:bg-gray-400/20 rounded-md"
              >
                movements
              </p>
              <p
                onClick={() => {
                  setShowMoves(false);
                  setShowChat(true);
                }}
                className="text-center uppercase w-1/2 hover:bg-gray-400/20 rounded-md"
              >
                CHAT
              </p>
            </div>
            <div
              id="moves"
              className={`moves-list ${showMoves ? "flex" : "hidden"} flex-col w-full h-[95%] max-h-[95%]`}
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
                    <div className="flex justify-center w-[16%] bg-mist-700 h-auto ">{`${i + 1}`}</div>
                    <div
                      id="mov-0"
                      data-fen={mov[0]?.fen}
                      onClick={() => showPrevMove("mov-0")}
                      className={`flex hover:bg-mist-500 cursor-pointer w-[42%] h-auto pl-2 ${movePairs[movePairs.length - 1][0]?.move == mov[0]?.move && !mov[1]?.move ? "bg-blue-400/50" : `${viewIndex === i * 2 ? 'bg-white text-black' : 'bg-mist-800'}`}`}
                    >{`${mov[0]?.move}`}</div>

                    <div
                      id="mov-1"
                      data-fen={mov[1]?.fen}
                      onClick={() => showPrevMove("mov-1")}
                      className={`flex w-[42%] ${mov[1]?.move ? "hover:bg-mist-500" : ""} cursor-pointer h-auto pl-2 ${movePairs[movePairs.length - 1][1]?.move == mov[1]?.move && mov[1]?.move ? "bg-blue-400/50" : `${viewIndex === i * 2 + 1 ? 'bg-white text-black' : 'bg-mist-800'}`}`}
                    >
                      {`${mov[1]?.move ? mov[1]?.move : ""}`}
                    </div>
                  </div>
                ))}
              </div>
              <div className="h-[10%] w-full flex flex-row justify-center items-center bg-mist-900/70 gap-3">
                <div className="flex justify-center items-center w-[15%] h-[60%] bg-mist-700/60 rounded-sm hover:bg-red-600/70 hover:scale-110 duration-300">
                  X
                </div>
                <div
                  onClick={() => sendResign()}
                  className="flex justify-center items-center w-[15%] h-[60%] bg-mist-700/60 rounded-sm hover:bg-red-600/50 hover:scale-110 duration-300"
                >
                  <Flag />
                </div>
              </div>
            </div>
            <div
              id="chat"
              className={`moves-list ${showChat ? "flex" : "hidden"} flex-col w-full h-[95%] max-h-[95%] overflow-y-scroll scroll-smooth `}
            >
              <div className="w-full h-[92%] flex justify-center items-center">
                <p>MESSAGE HERE</p>
              </div>
              <input
                type="text"
                placeholder="type your message here"
                className={`input input-primary w-full h-[8%] min-h-10 border-black border-t-2 rounded-b-md rounded-t-none`}
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
