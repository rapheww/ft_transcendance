import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Header from "../Navbar/Header";
import { useAuth } from "../AuthProvider";
import "/src/index.css";

const API = "http://127.0.0.1:8000";

type MatchResponse = {
  status: "waiting" | "matched";
  game_id?: number;
};

export default function Waiting() {
  const navigate = useNavigate();
  const { timer, bonus } = useParams<{
    timer: string;
    bonus: string;
  }>();
  const { token } = useAuth();

  const [error, setError] = useState("");
  const [waiting, setWaiting] = useState(true);
  const matched = useRef(false);

  const chrono = timer === "5" || timer === "10" ? Number(timer) : 5;
  const increment = bonus === "0" || bonus === "5" ? Number(bonus) : 0;

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }

    let cancelled = false;
    let timeout: ReturnType<typeof setTimeout> | undefined;

    const headers = {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };

    async function checkStatus(): Promise<boolean> {
      const response = await fetch(`${API}/api/matchmaking/status`, {
        headers,
      });

      if (!response.ok) {
        throw new Error("Could not check matchmaking status");
      }

      const data = (await response.json()) as MatchResponse | null;

      if (data?.status === "matched" && data.game_id != null) {
        if (!cancelled) {
          matched.current = true;
          setWaiting(false);
          navigate(`/chess/${chrono}/${increment}/${data.game_id}`, {
            replace: true,
          });
        }
        return true;
      }

      return false;
    }

    async function poll() {
      if (cancelled) return;

      try {
        if (await checkStatus()) return;
      } catch {
        if (!cancelled) {
          setError("Unable to check matchmaking. Retrying...");
        }
      }

      if (!cancelled) {
        timeout = setTimeout(poll, 1500);
      }
    }

    async function start() {
      try {
        const response = await fetch(`${API}/api/matchmaking/join`, {
          method: "POST",
          headers,
          body: JSON.stringify({
            initial_time_seconds: chrono * 60,
            increment_seconds: increment,
          }),
        });

        if (response.ok) {
          const data = (await response.json()) as MatchResponse;

          if (data.status === "matched" && data.game_id != null) {
            if (!cancelled) {
              matched.current = true;
              setWaiting(false);
              navigate(`/chess/${chrono}/${increment}/${data.game_id}`, {
                replace: true,
              });
            }
            return;
          }
        } else if (response.status !== 409) {
          throw new Error("Could not join matchmaking");
        }

        await poll();
      } catch {
        if (!cancelled) {
          setError("Unable to join matchmaking. Please try again.");
        }
      }
    }

    start();

    return () => {
      cancelled = true;
      if (timeout) clearTimeout(timeout);

      // Don't remove a queue entry after a successful match.
      if (!matched.current) {
        void fetch(`${API}/api/matchmaking/leave`, {
          method: "DELETE",
          headers: { Authorization: `Bearer ${token}` },
        }).catch(() => {});
      }
    };
  }, [token, navigate, chrono, increment]);

  return (
    <div>
      <Header />
      <div className="w-full min-h-[calc(100vh-56px)] flex flex-col justify-center items-center">
        <p className="uppercase text-3xl">
          {waiting ? "Waiting for opponent" : "Match found"}
        </p>

        {waiting && <div className="loader m-10" />}

        {error && <p role="alert">{error}</p>}

        <button onClick={() => navigate("/mode")} className="btn bg-mist-700 hover:bg-mist-600 m-5">
          Cancel
        </button>
      </div>
    </div>
  );
}