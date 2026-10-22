import { useEffect, useState } from "react";
import ChessPreview from "./Chess/preview/ChessPreview";
import { API } from "./Chess/utils/api";
import Header from "./Navbar/Header";
import { useNavigate } from "react-router-dom";

interface LeaderBoard {
  username: string;
  elo: number;
  wins: number;
  games_played: number;
}

const Home = () => {
  const navigate = useNavigate();
  const [leaderboard, SetLeaderboard] = useState<LeaderBoard[] | null>(null);

  async function getLeaderBoard() {
    try {
      const response = await fetch(`${API}/stats/leaderboard`);
      if (!response.ok) throw "need token";
      const infos = await response.json();
      if (!infos) return;
      SetLeaderboard(infos);
    } catch {
      return;
    }
  }

  useEffect(() => {
    getLeaderBoard();
  }, []);
  return (
    <div className="flex flex-col items-center min-h-screen">
      <Header />
      <div className="flex flex-col justify-center items-center flex-1 w-full px-4">
        <h1 className="text-4xl sm:text-6xl md:text-7xl m-6 sm:m-10 uppercase">
          Chess
        </h1>
        <div className="grid grid-cols-1 lg:grid-cols-3 items-center w-full gap-8 px-4">
          {leaderboard && (
            <div className="flex flex-col items-center justify-start w-full h-full p-3">
              <div className="w-full flex justify-center m-8">
                <h1>LeaderBoard</h1>
              </div>
              <div className="bg-black/20 backdrop-blur-xs w-[50%] max-h-50 md:max-h-75 overflow-y-auto overflow-x-hidden border-white/30 border flex flex-col items-center gap-2">
                {leaderboard.map((l, i) => (
                  <div key={i} className={`w-full h-10 md:h-15 flex flex-row justify-center items-center gap-1 ${i % 2 === 0 ? "bg-gray-50/5" : ""} p-2`}>
                    <p className="text-sm lg:text-lg">#{i + 1}</p>
                    <p className="text-sm lg:text-lg">{l.username}</p>
                    <p className="text-sm lg:text-lg">elo: {l.elo}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex flex-col items-center justify-center w-full min-w-0">
            <div className="w-full max-w-[50vh]">
              <ChessPreview dark={""} light={""} />
            </div>
            <div className="flex flex-col items-center m-6 sm:m-9 gap-4 w-full max-w-75">
              <button
                onClick={() => navigate("/mode")}
                className="
                relative z-0
                w-full h-13.5
                border-0 outline-none
                text-black
                bg-taupe-300
                cursor-pointer
                rounded-[10px]
                before:content-['']
                before:absolute
                before:-top-0.5 before:-left-0.5
                before:-z-10
                before:w-[calc(100%+4px)]
                before:h-[calc(100%+4px)]
                before:rounded-[10px]
                before:bg-[linear-gradient(45deg,#ff0000,#ff7300,#fffb00,#48ff00,#00ffd5,#002bff,#7a00ff,#ff00c8,#ff0000)]
                before:bg-size-[400%_400%]
                before:blur-[10px]
                before:opacity-0
                before:transition-opacity
                before:duration-300
                hover:before:opacity-100
                before:animate-[glowing_20s_linear_infinite]
                after:content-['']
                after:absolute
                after:inset-0
                after:-z-10
                after:w-full
                after:h-full
                after:rounded-[10px]
                after:bg-taupe-300
              "
              >
                Play
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
