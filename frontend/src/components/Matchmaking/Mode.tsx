import { useState } from "react";
import { useNavigate } from "react-router-dom";
import Header from "../Navbar/Header";
import { useAuth } from "../AuthProvider";

const API = "http://127.0.0.1:8000";

const modes = [
  { label: "5+0", timer: 5, bonus: 0 },
  { label: "10+0", timer: 10, bonus: 0 },
  { label: "10+5", timer: 10, bonus: 5 },
];

const difficulties = ["easy", "medium", "hard"] as const;

export default function Mode() {
  const navigate = useNavigate();
  const { token } = useAuth();

  const [selectedMode, setSelectedMode] = useState("5+0");
  const [difficulty, setDifficulty] =
    useState<"easy" | "medium" | "hard">("easy");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const selected = modes.find((mode) => mode.label === selectedMode)!;

  async function playAI() {
    if (!token || loading) {
      if (!token) navigate("/login");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API}/api/games/`, {
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

      navigate(
        `/chess/${selected.timer}/${selected.bonus}/${game.id}`,
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Could not start the game.",
      );
    } finally {
      setLoading(false);
    }
  }

  function playHuman() {
    navigate(
      `/matchmaking/${selected.timer}/${selected.bonus}`,
    );
  }

  return (
    <div>
      <Header />

      <main className="w-full min-h-[calc(100vh-56px)] flex flex-col justify-center items-center px-4">
        <h1 className="uppercase m-6 sm:m-10 text-lg tracking-wide">
          Select a game mode
        </h1>

        <div className="flex flex-wrap justify-center gap-3 mb-8">
          {modes.map((mode) => (
            <button
              key={mode.label}
              onClick={() => setSelectedMode(mode.label)}
              className={`btn border-none ${
                selectedMode === mode.label
                  ? "bg-blue-600"
                  : "bg-mist-700 hover:bg-mist-600"
              }`}
            >
              {mode.label}
            </button>
          ))}
        </div>

        <div className="flex flex-col sm:flex-row gap-6 w-full max-w-3xl">
          <section className="flex-1 rounded-lg bg-mist-800 p-6 flex flex-col items-center gap-4">
            <h2 className="text-xl font-semibold">
              Play against a human
            </h2>

            <p className="text-center text-sm opacity-80">
              Find an opponent with compatible time controls.
            </p>

            <button
              onClick={playHuman}
              className="btn bg-mist-700 hover:bg-mist-600 w-full"
            >
              Find opponent
            </button>
          </section>

          <section className="flex-1 rounded-lg bg-mist-800 p-6 flex flex-col items-center gap-4">
            <h2 className="text-xl font-semibold">
              Play against AI
            </h2>

            <label htmlFor="ai-difficulty">
              Difficulty
            </label>

            <select
              id="ai-difficulty"
              value={difficulty}
              onChange={(event) =>
                setDifficulty(
                  event.target.value as
                    | "easy"
                    | "medium"
                    | "hard",
                )
              }
              className="select select-bordered w-full"
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
              className="btn bg-mist-700 hover:bg-mist-600 w-full"
            >
              {loading ? "Creating game..." : "Play AI"}
            </button>
          </section>
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