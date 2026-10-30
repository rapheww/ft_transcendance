import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../Navbar/Header";
import { useAuth } from "../AuthProvider";
import { API } from "../Chess/utils/api";

// Keep the displayed time control and the values sent to the backend together.
const modes = [
  { label: "1+0", timer: 1, bonus: 0 },
  { label: "1+1", timer: 1, bonus: 1 },
  { label: "2+0", timer: 2, bonus: 0 },
  { label: "2+1", timer: 2, bonus: 1 },
  { label: "3+0", timer: 3, bonus: 0 },
  { label: "3+2", timer: 3, bonus: 2 },
  { label: "5+0", timer: 5, bonus: 0 },
  { label: "5+3", timer: 5, bonus: 3 },
  { label: "10+0", timer: 10, bonus: 0 },
  { label: "10+5", timer: 10, bonus: 5 },
  { label: "15+0", timer: 15, bonus: 0 },
  { label: "15+10", timer: 15, bonus: 10 },
];

const difficulties: string[] = ["easy", "medium", "hard"];

export default function Mode() {
  const navigate = useNavigate();
  const { token } = useAuth();

  const [selectedMode, setSelectedMode] = useState("5+0");
  const [difficulty, setDifficulty] = useState<"easy" | "medium" | "hard">(
    "easy",
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const selected = modes.find((mode) => mode.label === selectedMode)!;

  // AI games are created immediately; the returned ID is then used by the shared chess screen.
  async function playAI() {
    if (!token || loading) {
      if (!token) navigate("/login");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API}/games/`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          initial_time_seconds: selected.timer * 60,
          increment_seconds: selected.bonus,
          opponent_type: "ai",
          ai_difficulty: difficulty,
        }),
      });

      if (!response.ok) {
        throw new Error("Could not create the AI game.");
      }

      const game = await response.json();

      navigate(`/chess/${selected.timer}/${selected.bonus}/${game.id}`);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Could not start the game.",
      );
    } finally {
      setLoading(false);
    }
  }

  // Human games go through the queue, which finds an opponent with the same time control.
  function playHuman() {
    navigate(`/matchmaking/${selected.timer}/${selected.bonus}`);
  }

  return (
    <div>
      <Header />

      <main className="w-full min-h-[calc(100vh-56px)] flex flex-col justify-center items-center px-4 gap-5">
        <h1 className="uppercase m-6 sm:m-10 text-lg lg:text-2xl tracking-wide">
          Select a game mode
        </h1>

        <div className="w-full h-full flex flex-row items-center justify-center">
          <div className="grid grid-rows-3 h-full">
            <div className="opacity-40 text-center h-15 md:h-20 lg:h-25 [writing-mode:sideways-lr] text-md md:text-lg lg:text-2xl">
              BULLET
            </div>
            <div className="opacity-40 text-center  h-15 md:h-20 lg:h-25 [writing-mode:sideways-lr] text-md md:text-lg lg:text-2xl">
              BLITZ
            </div>
            <div className="  opacity-40 text-center h-15 md:h-20 lg:h-25 [writing-mode:sideways-lr] text-md md:text-lg lg:text-2xl">
              RAPID
            </div>
          </div>
          <div className="grid grid-cols-4 grid-rows-3 flex-wrap justify-center items-center gap-0.5 w-full lg:w-1/2">
            {modes.map((mode, i) => (
              <div
                key={i}
                className={`flex justify-center items-center w-full h-15 md:h-20 lg:h-25 border-white/30 border p-3 rounded-md ${selectedMode === mode.label ? "bg-white/10" : "bg-black/40 backdrop-blur-xs hover:bg-white/5"} backdrop-blur-xs hover:cursor-pointer`}
                onClick={() => setSelectedMode(mode.label)}
              >
                {mode.label}
              </div>
            ))}
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-6 w-full max-w-5xl mb-10">
          <div className="flex-1 rounded-md bg-black/20 backdrop-blur-xs border border-white/20 p-6 flex flex-col items-center gap-4">
            <h2 className="text-xl font-semibold">Play against a human</h2>

            <p className="text-center text-sm opacity-80 mt-auto">
              Find an opponent with compatible time controls.
            </p>
            <button
              type="submit"
              id="log-btn"
              onClick={playHuman}
              className="relative inline-flex items-center justify-center mt-auto px-6 py-2 lg:px-10 lg:py-3 lg:text-md overflow-hidden  text-white hover:text-gray-700 rounded-md shadow-2xl group"
            >
              <span className="absolute inset-0 w-full h-full transition duration-350 ease-in opacity-0 bg-linear-to-br from-white via-gray-200 to-white group-hover:opacity-100"></span>
              <span className="absolute top-0 left-0 w-full bg-linear-to-b from-white to-transparent opacity-5 h-1/3"></span>
              <span className="absolute bottom-0 left-0 w-full h-1/3 bg-linear-to-t from-white to-transparent opacity-5"></span>
              <span className="absolute bottom-0 left-0 w-4 h-full bg-linear-to-r from-white to-transparent opacity-5"></span>
              <span className="absolute bottom-0 right-0 w-4 h-full bg-linear-to-l from-white to-transparent opacity-5"></span>
              <span className="absolute inset-0 w-full h-full border  roflex max-h-75 ex-col gap-2 overflow-y-auto overflow-x-hidden border-white/30 bg-black/20 p-2 backdrop-blur-xsunded-md opacity-10"></span>
              <span className="absolute w-0 h-0 transition-all duration-350 ease-out bg-white rounded-full group-hover:w-56 group-hover:h-56 opacity-5"></span>
              <span className="relative">Find opponent</span>
            </button>
          </div>

          <div className="flex-1 rounded-md bg-black/20 backdrop-blur-xs border border-white/20 p-6 flex flex-col items-center gap-4">
            <h2 className="text-xl font-semibold">Play against AI</h2>

            <label htmlFor="ai-difficulty">Difficulty</label>

            <select
              id="ai-difficulty"
              value={difficulty}
              onChange={(event) =>
                setDifficulty(event.target.value as "easy" | "medium" | "hard")
              }
              className="select w-full outline-0 bg-white/3 focus:border-white/50 focus-within:border-white/50"
            >
              {difficulties.map((level) => (
                <option key={level} value={level}>
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </option>
              ))}
            </select>
            <button
              onClick={playAI}
              disabled={loading}
              type="submit"
              id="log-btn"
              className="relative inline-flex items-center justify-center mt-auto px-10 py-2 lg:px-15 lg:py-3 lg:text-md overflow-hidden text-white hover:text-gray-700 rounded-md shadow-2xl group"
            >
              <span className="absolute inset-0 w-full h-full transition duration-350 ease-in opacity-0 bg-linear-to-br from-white via-gray-200 to-white group-hover:opacity-100"></span>
              <span className="absolute top-0 left-0 w-full bg-linear-to-b from-white to-transparent opacity-5 h-1/3"></span>
              <span className="absolute bottom-0 left-0 w-full h-1/3 bg-linear-to-t from-white to-transparent opacity-5"></span>
              <span className="absolute bottom-0 left-0 w-4 h-full bg-linear-to-r from-white to-transparent opacity-5"></span>
              <span className="absolute bottom-0 right-0 w-4 h-full bg-linear-to-l from-white to-transparent opacity-5"></span>
              <span className="absolute inset-0 w-full h-full border border-white rounded-md opacity-10"></span>
              <span className="absolute w-0 h-0 transition-all duration-350 ease-out bg-white rounded-full group-hover:w-56 group-hover:h-56 opacity-5"></span>
              <span className="relative">
                {loading ? "Creating game..." : "Play AI"}
              </span>
            </button>
          </div>
        </div>

        {error && (
          <p role="alert" className="text-red-400 mt-5">
            {error}
          </p>
        )}
      </main>
    </div>
  );
}
