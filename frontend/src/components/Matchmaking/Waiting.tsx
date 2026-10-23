import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import Header from "../Navbar/Header";
import { useAuth } from "../AuthProvider";
import "/src/index.css";
import { API } from "../Chess/utils/api";

export const allTime = ['1+0', '1+1', '2+0', '2+1', '3+0', '3+2', '5+0', '5+3', '10+0', '10+5', '15+0', '15+10']

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
  const leaveTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const time: string = timer + "+" + bonus
  let i = 0;
  let chrono = 5;
  let increment = 5;
  for (; i < allTime.length; i++)
    if(allTime[i] === time) break;
  if(allTime[i]){
    chrono = Number(timer);
    increment = Number(bonus);
  }

  useEffect(() => {
    if (!token) {
      navigate("/login");
      return;
    }

    if (leaveTimeout.current !== null) {
      clearTimeout(leaveTimeout.current);
      leaveTimeout.current = null;
    }

    let cancelled = false;
    let timeout: ReturnType<typeof setTimeout> | undefined;

    const headers = {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    };

    // Polling detects a match when the opponent is assigned asynchronously.
    async function checkStatus(): Promise<boolean> {
      const response = await fetch(`${API}/matchmaking/status`, {
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

    // A join can return a match immediately; 409 means stay in the existing queue and poll status.
    async function start() {
      try {
        const response = await fetch(`${API}/matchmaking/join`, {
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
        // Defer leaving by one task so a quick effect restart can cancel cleanup instead.
        leaveTimeout.current = setTimeout(() => {
          leaveTimeout.current = null;
          void fetch(`${API}/matchmaking/leave`, {
            method: "DELETE",
            headers: { Authorization: `Bearer ${token}` },
          }).catch(() => {});
        }, 0);
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

        <button
          onClick={() => navigate("/mode")}
          className="btn bg-mist-700 hover:bg-mist-600 m-5"
        >
          Cancel
        </button>
      </div>
    </div>
  );
}
