import Header from "../Navbar/Header";
import { useState } from "react";
import Chessboard from "./Chessboard";

export default function Chess() {
  const [moves, setMoves] = useState<string[]>([]);
  return (
    <div className="w-full min-h-screen">
      <Header />

      <main className="min-h-[calc(100vh-72px)] flex items-center justify-center px-4">
        <div className="flex items-stretch justify-center gap-4 lg:gap-6 w-full max-w-450">
          <div
            id="mov-resume"
            className={`hidden 
            md:flex 
            order-1 
            shrink-0 
            w-70 
            lg:w-100 
            h-[min(800px,90vw,calc(100vh-140px))] 
            rounded-md
            border-2
            border-black
            shadow-[0_0_6px_#000000]
            bg-mist-800 
            items-center 
            justify-center 
            flex-col
            `}
          >
            <div className={`border-b-2 border-black w-full h-[5%] flex items-center justify-center`}>
              <p className="text-center uppercase">movements</p>
            </div>
            <div className="moves-list w-full h-[95%] max-h-[95%] overflow-scroll">
              {moves.map((mov, i) => (
                <p key={i} className="text-center">
                  {mov}
                </p>
              ))}
            </div>
          </div>

          <div className={`order-2 flex-1 min-w-0 flex justify-center`}>
            <Chessboard setMoves={setMoves} />
          </div>

          <div
            id="chat"
            className="
            hidden
            xl:flex
            order-3
            shrink-0 
            w-110 
            border-2
            border-black
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
                className={`input input-primary w-full h-full border-black border-t-2 rounded-none`}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
