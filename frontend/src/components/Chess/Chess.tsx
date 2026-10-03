import Header from "../Navbar/Header";
import { useEffect, useMemo, useRef, useState } from "react";
import Chessboard from "./Chessboard";

export default function Chess() {
  const [moves, setMoves] = useState<string[]>([]);
  const movesListRef = useRef<HTMLDivElement>(null);

  const movePairs = useMemo(() => {
    let tmp:string[][] = [];
    let j = 0;
    for(let i = 0; i< moves.length; i+=2){
      tmp[j] = []
        tmp[j].push(moves[i], moves[i + 1])
        j++;
    }
    return tmp
  }, [moves])
  useEffect(() => {
    if(movesListRef.current){
      movesListRef.current.scrollTop = movesListRef.current.scrollHeight; //defini la hauteur a scroll par la hauteur actuelle de l'element
    }
  },[moves] )

  return (
    <div className="w-full min-h-screen">
      <Header />

      <main className="min-h-[calc(100vh-72px)] flex items-center justify-center px-4">
        <div className="flex items-stretch gap-2 justify-center w-full max-w-470 h-[min(900px,90vw,calc(100vh-140px))]">
          <div
            id="mov-resume"
            className={`hidden 
            md:flex 
            order-1 
            shrink-0 
            sm:w-0
            md:w-[19%]
            lg:w-[25%]
            xl:w-[25%] 
            h-[min(800px,90vw,calc(100vh-140px))] 
            rounded-md
            shadow-[0_0_6px_#000000]
            bg-mist-800 
            items-center 
            justify-center 
            flex-col
            `}
          >
            <div className={`border-b-2 border-black w-full h-[5%] flex items-center justify-center rounded-t-md p-2`}>
              <p className="text-center uppercase w-1/2 hover:bg-gray-400/20 rounded-md">movements</p>
              <p className="text-center uppercase w-1/2 hover:bg-gray-400/20 rounded-md">CHAT</p>
            </div>
            <div ref={movesListRef} className="moves-list flex flex-col w-full h-[95%] max-h-[95%] overflow-y-scroll scroll-smooth">
              {movePairs.map((mov, i) => (
                <div key={i} className="flex flex-row w-full justify-center text-justify">
                  <div className="flex justify-center w-[16%] bg-mist-700 ">{`${i + 1}`}</div>
                  <div className="flex hover:bg-mist-500 cursor-pointer w-[42%] pl-2">{`${mov[0]}`}</div>
                  <div className={`flex w-[42%] hover:bg-mist-500 cursor-pointer pl-2`}>{`${mov[1] ? mov[1] : ""}`}</div>
                </div>
              ))}
            </div>
          </div>

          <div className={`order-2 flex-1 min-w-0 flex items-center justify-center @container-size`}>
            <Chessboard setMoves={setMoves} />
          </div>

          <div
            id="chat"
            className="
            hidden
            xl:flex
            order-3
            shrink-0
            sm:w-0
            md:w-0
            lg:w-0
            xl:w-[15%]
            2xl:w-[25%]
            shadow-[0_0_6px_#000000]
            rounded-md 
            bg-mist-800 
            items-center 
            justify-center
            flex-col
            "
          >
            <div className={`border-b-2 border-black w-full h-[5%] flex items-center justify-center`}>
              <p className="text-center uppercase">Chat</p>
            </div>
            <div className=" w-full h-[87%]"></div>
            <div className="w-full h-[8%]">
              <input
                type="text"
                placeholder="type your message here"
                className={`input input-primary w-full h-full border-black border-t-2 rounded-b-md rounded-t-none`}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
