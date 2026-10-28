import { useEffect, useState } from "react";
import ChessPreview from "./Chess/preview/ChessPreview";
import { API } from "./Chess/utils/api";
import { getUserIdFromToken } from "./Chess/utils/game";
import Header from "./Navbar/Header";
import { useNavigate } from "react-router-dom";
import { useAuth } from "./AuthProvider";

interface LeaderBoard {
  username: string;
  elo: number;
  wins: number;
  games_played: number;
}

interface OngoingGame {
  id: number;
  white_player_id: number;
  black_player_id: number | null;
  white_player_name: string;
  black_player_name: string | null;
  opponent_type: string;
  ai_difficulty: string | null;
  initial_time_seconds: number | null;
  increment_seconds: number;
}

const Home = () => {
  const navigate = useNavigate();
  const { token } = useAuth();
  const currentUserId = token ? getUserIdFromToken(token) : null;
  const [leaderboard, SetLeaderboard] = useState<LeaderBoard[] | null>(null);
  const [ongoingGames, setOngoingGames] = useState<OngoingGame[]>([]);
  const [gamesError, setGamesError] = useState("");

  useEffect(() => {
    let cancelled = false;

    async function getLeaderBoard() {
      try {
        const response = await fetch(`${API}/stats/leaderboard`);
        if (!response.ok) throw new Error("Could not load leaderboard.");
        const infos = await response.json();
        if (!cancelled && infos) SetLeaderboard(infos);
      } catch {
        if (!cancelled) SetLeaderboard(null);
      }
    }

    void getLeaderBoard();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function getOngoingGames() {
      try {
        const response = await fetch(`${API}/games/ongoing`);
        if (!response.ok) {
          throw new Error(`Could not load ongoing games (${response.status}).`);
        }
        const games = (await response.json()) as OngoingGame[];
        if (!cancelled) {
          setOngoingGames(games);
          setGamesError("");
        }
      } catch (error) {
        if (!cancelled) {
          setGamesError(
            error instanceof Error
              ? error.message
              : "Could not load ongoing games.",
          );
        }
      }
    }

    void getOngoingGames();
    const interval = window.setInterval(() => void getOngoingGames(), 15000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, []);

  return (
    <div className="flex flex-col items-center min-h-screen">
      <Header />
      <div className="flex flex-col justify-center items-center flex-1 w-full px-4">
        <h1 className="text-4xl sm:text-6xl md:text-7xl m-6 sm:m-10 uppercase flex flex-row">
          42<p className={`text-sky-400`}>Chess</p>
        </h1>
        <div className="grid grid-cols-1 lg:grid-cols-3 items-center w-full gap-8 px-4">
          {leaderboard && (
            <div className="flex flex-col items-center justify-start w-full h-full p-3">
              <div className="w-full flex justify-center m-8">
                <h1 className="text-lg lg:text-xl">LeaderBoard</h1>
              </div>
              <div className="bg-black/20 backdrop-blur-xs w-[70%] max-h-50 md:max-h-75 overflow-y-auto overflow-x-hidden border-white/30 border flex flex-col items-center gap-2 p-2 ">
                {leaderboard.map((l, i) => (
                  <div
                    key={i}
                    className={`w-full h-10 md:h-15 flex flex-row justify-center items-center gap-1 ${i % 2 === 0 ? "bg-gray-50/5" : ""} p-2 rounded-sm`}
                  >
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

          <div className="flex h-full w-full flex-col items-center justify-start p-3">
            <div className="m-8 flex w-full items-center justify-center gap-3">
              <h2 className="text-lg lg:text-xl">Ongoing matches</h2>

              <span className="relative flex">
                <span className="absolute inline-flex h-full w-full animate-soft-ping rounded-full bg-red-500 opacity-30"></span>
                <span className="relative rounded-full bg-red-500/15 px-5 py-1 text-sm font-semibold text-red-300">
                  {ongoingGames.length} LIVE
                </span>
              </span>
            </div>
            <div className="bg-black/20 backdrop-blur-xs w-[70%] max-h-50 md:max-h-75 overflow-y-auto overflow-x-hidden border-white/30 border flex flex-col items-center gap-2 p-2 ">
              {gamesError ? (
                <p
                  role="alert"
                  className="p-3 text-center text-sm text-red-300"
                >
                  {gamesError}
                </p>
              ) : ongoingGames.length === 0 ? (
                <p className="p-3 text-center text-sm text-gray-300">
                  No ongoing matches right now.
                </p>
              ) : (
                ongoingGames.map((game) => {
                  const canResume =
                    currentUserId !== null &&
                    (game.white_player_id === currentUserId ||
                      game.black_player_id === currentUserId);
                  const blackName =
                    game.black_player_name ||
                    (game.opponent_type === "ai" ? "Computer" : "Black");
                  const timeControl =
                    game.initial_time_seconds === null
                      ? "Untimed"
                      : `${Math.floor(game.initial_time_seconds / 60)}+${game.increment_seconds}`;

                  return (
                    <button
                      key={game.id}
                      type="button"
                      onClick={() => {
                        if (canResume) {
                          const minutes =
                            game.initial_time_seconds === null
                              ? 5
                              : game.initial_time_seconds / 60;
                          navigate(
                            `/chess/${minutes}/${game.increment_seconds}/${game.id}`,
                          );
                        } else {
                          navigate(`/watch/${game.id}`);
                        }
                      }}
                      className="flex w-full items-center justify-between gap-3 rounded-sm bg-gray-50/5 p-3 text-left transition-colors hover:bg-gray-50/15"
                    >
                      <span className="min-w-0">
                        <span className="block truncate text-sm font-semibold">
                          {game.white_player_name} vs {blackName}
                        </span>
                        <span className="mt-1 block text-xs text-gray-400">
                          {timeControl}
                          {game.opponent_type === "ai" &&
                            game.ai_difficulty &&
                            ` · ${game.ai_difficulty} AI`}
                        </span>
                      </span>
                      <span className="shrink-0 rounded-full bg-red-500/15 px-2 py-1 text-[10px] font-bold tracking-wider text-red-300">
                        {canResume ? "RESUME" : "WATCH"}
                      </span>
                    </button>
                  );
                })
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Home;
