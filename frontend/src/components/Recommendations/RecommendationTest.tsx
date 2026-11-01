import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import type {
  OpponentRecommendation,
  RecommendationResponse,
} from "./recommendation";
import {
  botLevel,
  getRecommendations,
  startBotGame,
  toMatchPercent,
} from "./recommendationApi";
import { useAuth } from "../AuthProvider";
import Header from "../Navbar/Header";

type Tab = "bots" | "humans";

function OpponentRow({
  player,
  onPlay,
  busy,
}: {
  player: OpponentRecommendation;
  onPlay: (p: OpponentRecommendation) => void;
  busy: boolean;
}) {
  const match = toMatchPercent(player.similarity_score);
  return (
    <li className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5 transition">

      <div className="flex-1 min-w-0">
        <p className="truncate">
          {player.username}
          {player.is_bot && (
            <span className="ml-2 text-xs opacity-50">{botLevel(player)}</span>
          )}
        </p>
        {match !== null && (
          <div className="flex items-center gap-2 mt-1">
            <div className="h-1 w-24 sm:w-32 rounded-full bg-white/10 overflow-hidden">
              <div
                className="h-full rounded-full bg-white/70"
                style={{ width: `${match}%` }}
              />
            </div>
            <span className="text-xs opacity-60">{match}%</span>
          </div>
        )}
      </div>

      <span className="px-2 py-0.5 rounded-full border border-white/20 text-xs tabular-nums whitespace-nowrap">
        {player.elo} Elo
      </span>

      {player.is_bot && (
        //ICI A CHANGER
        <button
          onClick={() => onPlay(player)}
          disabled={busy}
          className="px-3 py-1 text-sm rounded-md border border-white/30 hover:bg-white hover:text-gray-700 transition duration-350 cursor-pointer disabled:opacity-40"
        >
          Play
        </button>
      )}
    </li>
  );
}

// The card itself. Later, the profile page only needs: <RecommendationCard />
export function RecommendationCard({ topN = 5 }: { topN?: number }) {
  const { token } = useAuth();
  const navigate = useNavigate();

  const [recommendations, setRecommendations] =
    useState<RecommendationResponse>({ humans: [], bots: [] });
  const [tab, setTab] = useState<Tab>("bots");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let cancelled = false;
    async function loadRecommendations() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        setLoading(true);
        setError(null);
        const data = await getRecommendations(token, topN);
        if (!cancelled) setRecommendations(data);
      } catch {
        if (!cancelled) setError("Could not load recommendations.");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    loadRecommendations();
    return () => {
      cancelled = true;
    };
  }, [token, topN]);

  async function playBot(bot: OpponentRecommendation) {
    if (!token || busy) return;
    setBusy(true);
    try {
      const gameId = await startBotGame(token, bot);
      navigate(`/chess/5/0/${gameId}`);
    } catch {
      setError("Could not start the game.");
      setBusy(false);
    }
  }

  const list = recommendations[tab];

  return (
    <div className="w-full h-full bg-white/3 rounded-md flex flex-col">
      <div className="flex items-center justify-between gap-2 p-2 px-4 border-b">
        <h1 className="font-bold flex items-center gap-2 whitespace-nowrap">
          {/* Desktop: "SUGGESTED OPPONENTS" / mobile: "OPPONENTS" */}
          <span>
            <span className="hidden sm:inline">SUGGESTED </span>OPPONENTS
          </span>
        </h1>
        <div className="flex text-sm rounded-md border border-white/30 overflow-hidden whitespace-nowrap">
          {(["bots", "humans"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-3 py-1 cursor-pointer transition ${tab === t ? "bg-white/15" : "hover:bg-white/5 opacity-60"}`}
            >
              {t === "bots" ? "Bots" : "Players"} ({recommendations[t].length})
            </button>
          ))}
        </div>
      </div>

      <div className="p-2 flex-1">
        {loading ? (
          <div className="flex justify-center p-6">
            <span className="loading loading-dots loading-md" />
          </div>
        ) : error ? (
          <p className="p-4 text-center text-red-400">{error}</p>
        ) : list.length === 0 ? (
          <p className="p-4 text-center opacity-60">
            No one near your level yet ...
          </p>
        ) : (
          <ul className="flex flex-col gap-1">
            {list.map((p) => (
              <OpponentRow
                key={p.user_id}
                player={p}
                onPlay={playBot}
                busy={busy}
              />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

// Test page at /test-recommendations, same frame as the profile page.
export default function RecommendationTest() {
  return (
    <div>
      <Header />
      <div className="w-full min-h-[calc(100vh-56px)] flex justify-center items-center py-6">
        <div className="w-[92%] md:w-[85%] xl:w-[75%] bg-black/20 backdrop-blur-xs rounded-md border border-white/15 p-4">
          <RecommendationCard topN={5} />
        </div>
      </div>
    </div>
  );
}
