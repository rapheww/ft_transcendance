import Header from "../Navbar/Header";
import { useEffect, useMemo, useRef, useState } from "react";
import Chessboard from "./Chessboard";
import { Flag } from "lucide-react";
import Timer from "./Timer";
import { useParams } from "react-router-dom";
import { useAuth } from "../AuthProvider";
import ProfilePreview from "./ProfilePreview";

export default function Chess() {
  const [showMoves, setShowMoves] = useState<boolean>(true);
  const [showChat, setShowChat] = useState<boolean>(false);
  const [bTurn, setBturn] = useState<boolean>(false);
  const [wTurn, setWturn] = useState<boolean>(false);
  const [moves, setMoves] = useState<string[]>([]);
  const [wBonus, setWBonus] = useState<boolean>(false);
  const [bBonus, setBBonus] = useState<boolean>(false);
  const [open, setOpen] = useState<boolean>(false);
  const [username, setUsername] = useState<string>("");
  const movesListRef = useRef<HTMLDivElement>(null);
  const { timer, bonus } = useParams<{ timer: string; bonus: string }>();
  const add = bonus === "0" || bonus === "5" ? Number(bonus) : 0;
  const chrono = timer === "5" || timer === "10" ? Number(timer) : 0;

  const { user } = useAuth();
  //a delete
  const user1 = "Bob";

  const movePairs = useMemo(() => {
    let tmp: string[][] = [];
    let j = 0;
    for (let i = 0; i < moves.length; i += 2) {
      tmp[j] = [];
      tmp[j].push(moves[i], moves[i + 1]);
      j++;
    }
    return tmp;
  }, [moves]);
  useEffect(() => {
    if (movesListRef.current) {
      movesListRef.current.scrollTop = movesListRef.current.scrollHeight; //defini la hauteur a scroll par la hauteur actuelle de l'element
    }
  }, [moves]);

  return (
    <div className="w-full min-h-screen">
      <Header />

      <main className="min-h-[calc(100dvh-72px)] flex items-center justify-center px-2 md:px-4">
        <div className="flex flex-col md:flex-row lg:grid lg:grid-cols-[1fr_auto_1fr] items-center md:items-stretch lg:items-center gap-2 md:gap-3 justify-center w-full max-w-470 md:h-[calc(100dvh-72px-2rem)]">
          <div className="flex flex-col h-full w-full justify-center items-center order-1 lg:col-start-2 lg:row-start-1 lg:-translate-x-20 gap-2 md:w-auto md:h-full md:max-w-[calc(100%-clamp(240px,26vw,420px)-0.75rem)] md:shrink lg:h-auto lg:max-w-none">
            <div className="flex flex-row justify-between items-center w-full h-10 shrink-0 p-3 rounded-sm bg-mist-400/10">
              <p
                onClick={() => {
                  setOpen(true)
                  if (user1)
                    setUsername(user1)
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
                />
              </div>
              {/* time a changer en fonction du mode donc passage en props */}
            </div>
            <div className="w-full aspect-square max-h-[65dvh] md:max-h-none md:h-auto md:w-[calc(100dvh-72px-8rem)] lg:h-auto lg:w-[min(calc(100dvh-72px-8rem),calc(100vw-2*clamp(240px,26vw,420px)-14.5rem))] flex items-center justify-center @container-size">
              <Chessboard
                setMoves={setMoves}
                setBTurn={setBturn}
                setWTurn={setWturn}
                setBBonus={setBBonus}
                setWBonus={setWBonus}
              />
            </div>
            <div className="flex flex-row justify-between items-center w-full h-10 shrink-0 p-3 rounded-sm bg-mist-400/10">
              <p
                onClick={() => {
                  setOpen(true)
                  if (user)
                    setUsername(user)
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
                      className={`flex hover:bg-mist-500 cursor-pointer w-[42%] h-auto pl-2 ${movePairs[movePairs.length - 1][0] == mov[0] && !mov[1] ? "bg-blue-400/50" : "bg-mist-800"}`}
                    >{`${mov[0]}`}</div>

                    <div
                      className={`flex w-[42%] ${mov[1] ? "hover:bg-mist-500" : ""} cursor-pointer h-auto pl-2 ${movePairs[movePairs.length - 1][1] == mov[1] && mov[1] ? "bg-blue-400/50" : "bg-mist-800"}`}
                    >
                      {`${mov[1] ? mov[1] : ""}`}
                    </div>
                  </div>
                ))}
              </div>
              <div className="h-[10%] w-full flex flex-row justify-center items-center bg-mist-900/70 gap-3">
                <div className="flex justify-center items-center w-[15%] h-[60%] bg-mist-700/60 rounded-sm hover:bg-red-600/70 hover:scale-110 duration-300">
                  X
                </div>
                <div className="flex justify-center items-center w-[15%] h-[60%] bg-mist-700/60 rounded-sm hover:bg-red-600/50 hover:scale-110 duration-300">
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
        <ProfilePreview onClose={() => setOpen(false)} open={open} username={username}/>
      </main>
    </div>
  );
}
