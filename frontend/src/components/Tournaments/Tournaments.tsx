import { useEffect, useState, type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { Bot, Crown, Plus, Swords, Trophy, Users } from "lucide-react";
import Header from "../Navbar/Header";
import { useAuth } from "../AuthProvider";
import {
    createTournament,
    fillWithBots,
    getMyTournament,
    getTournamentBots,
    getTournament,
    joinTournament,
    listTournaments,
    startTournament,
} from "./tournamentApi";
import type { BotInfo, Tournament } from "./tournamentTypes";
import TournamentBracket from "./TournamentBracket";

// How often the page asks the backend for news (the scheduler changes rounds by itself).
const REFRESH_MS = 3000;
// Tournament games are 10+0 (TOURNAMENT_INITIAL_TIME_SECONDS in tournament_service.py).
const GAME_MINUTES = 10;
const GAME_BONUS = 0;

// We remember the last tournament so its result stays visible after it ends
// (/api/tournaments/me only returns tournaments that are still running).
const LAST_KEY = "lastTournamentId";
function readLastId(): number | null {
    try {
        const v = Number(localStorage.getItem(LAST_KEY));
        return Number.isInteger(v) && v > 0 ? v : null;
    } catch {
        return null;
    }
}
function saveLastId(id: number) {
    try {
        localStorage.setItem(LAST_KEY, String(id));
    } catch {
        /* storage unavailable: the result just won't stay after the end */
    }
}
function clearLastId() {
    try {
        localStorage.removeItem(LAST_KEY);
    } catch {
        /* ignore */
    }
}

// 125000 ms -> "2:05"
function formatLeft(targetIso: string | null, now: number): string {
    if (!targetIso) return "--:--";
    const ms = Math.max(0, new Date(targetIso).getTime() - now);
    const s = Math.ceil(ms / 1000);
    return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`;
}

function isExpired(t: Tournament, now: number): boolean {
    return t.status === "registration" && new Date(t.registration_deadline).getTime() <= now;
}

const STATUS_LABEL: Record<string, string> = {
    registration: "Registration",
    countdown: "Starting soon",
    in_progress: "In progress",
    between_rounds: "Next round soon",
    finished: "Finished",
    cancelled: "Cancelled",
};

// Same card style as HISTORY / SUGGESTED OPPONENTS on the profile page.
function Card({ icon, title, right, children }: {
    icon: ReactNode;
    title: string;
    right?: ReactNode;
    children: ReactNode;
}) {
    return (
        <div className="w-full bg-white/3 rounded-md flex flex-col">
            <div className="flex items-center justify-between gap-2 p-2 px-4 border-b">
                <h1 className="font-bold flex items-center gap-2 whitespace-nowrap">
                    {icon} {title}
                </h1>
                {right}
            </div>
            {children}
        </div>
    );
}

const buttonClass =
    "px-3 py-1 text-sm rounded-md border border-white/30 hover:bg-white hover:text-gray-700 transition duration-350 cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:bg-transparent disabled:hover:text-inherit";

export default function Tournaments() {
    const { token, user, profil } = useAuth();
    const navigate = useNavigate();
    const myName = profil.username || user || "";

    const [tournament, setTournament] = useState<Tournament | null>(null); // the one I am in (or just finished)
    const [openList, setOpenList] = useState<Tournament[]>([]); // tournaments I can join
    const [loading, setLoading] = useState(true);
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null); // error from Create / Join / Start
    const [offline, setOffline] = useState(false); // the automatic refresh failed
    const [reloadKey, setReloadKey] = useState(0);
    const [now, setNow] = useState(() => Date.now());
    // ADDED (optional bots): bots of the shown tournament, and the organizer's choice at Start
    const [bots, setBots] = useState<BotInfo[]>([]);
    const [withBots, setWithBots] = useState(false); // "Humans only" by default

    // Clock for the countdowns
    useEffect(() => {
        const id = window.setInterval(() => setNow(Date.now()), 1000);
        return () => window.clearInterval(id);
    }, []);

    // Load my tournament (or the open list), then refresh every few seconds
    useEffect(() => {
        if (!token) return;
        let cancelled = false;

        async function refresh() {
            try {
                const mine = await getMyTournament(token);
                let shown: Tournament | null = mine;
                if (mine) {
                    saveLastId(mine.id);
                } else {
                    // Not in a running tournament: maybe the last one just ended
                    const lastId = readLastId();
                    if (lastId) {
                        try {
                            const last = await getTournament(lastId, token);
                            const ended = last.status === "finished" || last.status === "cancelled" || isExpired(last, Date.now());
                            if (ended) shown = last;
                            else clearLastId();
                        } catch {
                            clearLastId();
                        }
                    }
                }
                const open = shown ? [] : await listTournaments(token);
                const botList = shown ? await getTournamentBots(shown.id, token).catch(() => []) : [];
                if (cancelled) return;
                setTournament(shown);
                setOpenList(open);
                setBots(botList);
                setOffline(false);
            } catch {
                if (!cancelled) setOffline(true);
            } finally {
                if (!cancelled) setLoading(false);
            }
        }

        refresh();
        const id = window.setInterval(refresh, REFRESH_MS);
        return () => {
            cancelled = true;
            window.clearInterval(id);
        };
    }, [token, reloadKey]);

    // Create / Join / Start: same handling for the three buttons
    async function act(action: () => Promise<Tournament>) {
        if (busy) return;
        setBusy(true);
        setError(null);
        try {
            const t = await action();
            saveLastId(t.id);
            setTournament(t);
            setReloadKey((k) => k + 1);
        } catch (err) {
            setError(err instanceof Error ? err.message : "Something went wrong.");
        } finally {
            setBusy(false);
        }
    }

    function backToList() {
        clearLastId();
        setTournament(null);
        setError(null);
        setLoading(true);
        setReloadKey((k) => k + 1);
    }

    // ---------- views ----------

    function Lobby() {
        return (
            <Card
                icon={<Trophy size={16} />}
                title="TOURNAMENTS"
                right={
                    <button className={`${buttonClass} flex items-center gap-1`} disabled={busy} onClick={() => act(() => createTournament(token))}>
                        <Plus size={14} /> Create
                    </button>
                }
            >
                {openList.length === 0 ? (
                    <p className="p-4 text-center opacity-60">No open tournament yet ... create one!</p>
                ) : (
                    <ul className="flex flex-col gap-1 p-2">
                        {openList.map((t) => {
                            const organizer =
                                t.organizer_type === "api"
                                    ? "Public API"
                                    : t.participant_details.find((p) => p.id === t.creator_id)?.username ?? "?";
                            return (
                                <li key={t.id} className="flex items-center gap-3 px-3 py-2 rounded-md hover:bg-white/5 transition">
                                    <div className="w-9 h-9 shrink-0 rounded-full bg-white/10 border border-white/20 flex items-center justify-center">
                                        <Trophy size={16} />
                                    </div>
                                    <div className="flex-1 min-w-0">
                                        <p className="truncate">Tournament #{t.id}</p>
                                        <p className="text-xs opacity-50 truncate">by {organizer} · closes in {formatLeft(t.registration_deadline, now)}</p>
                                    </div>
                                    <span className="px-2 py-0.5 rounded-full border border-white/20 text-xs whitespace-nowrap flex items-center gap-1">
                                        <Users size={12} /> {t.participant_count}
                                    </span>
                                    <button className={buttonClass} disabled={busy} onClick={() => act(() => joinTournament(t.id, token))}>
                                        Join
                                    </button>
                                </li>
                            );
                        })}
                    </ul>
                )}
                <p className="px-4 pb-3 text-xs opacity-40 text-center">
                    Knockout · {GAME_MINUTES} min games · the organizer starts it, with humans only or with AI bots
                </p>
            </Card>
        );
    }

    function TournamentView({ t }: { t: Tournament }) {
        const botById = new Map(bots.map((b) => [b.id, b]));
        const botLabel = (b: BotInfo) => `AI · ${b.ai_level ?? "medium"} · ${b.elo}`;
        const me = t.participant_details.find((p) => p.username === myName);
        const myId = me?.id ?? null;
        const isOrganizer = myId !== null && t.organizer_type === "player" && t.creator_id === myId;
        const totalRounds = Math.max(0, ...t.matches.map((m) => m.round));
        const myMatch = t.matches.find(
            (m) => m.round === t.current_round && myId !== null && (m.player1_id === myId || m.player2_id === myId),
        );
        const winnerName = t.participant_details.find((p) => p.id === t.winner_id)?.username;
        const cancelled = t.status === "cancelled" || isExpired(t, now);
        const ended = t.status === "finished" || cancelled;

        // One line that says what is happening right now
        let statusLine: ReactNode = null;
        if (cancelled) statusLine = "Registration closed before the tournament started.";
        else if (t.status === "registration") statusLine = `Waiting for players · registration closes in ${formatLeft(t.registration_deadline, now)}`;
        else if (t.status === "countdown") statusLine = `Round 1 starts in ${formatLeft(t.next_round_at, now)}`;
        else if (t.status === "between_rounds") statusLine = `Round ${t.current_round + 1} starts in ${formatLeft(t.next_round_at, now)}`;
        else if (t.status === "in_progress") statusLine = `Round ${t.current_round} of ${totalRounds} in progress`;

        // What *I* should do now
        let myAction: ReactNode = null;
        if (t.my_game_id) {
            const opponentId = myMatch ? (myMatch.player1_id === myId ? myMatch.player2_id : myMatch.player1_id) : null;
            const opponent = t.participant_details.find((p) => p.id === opponentId);
            const opponentBot = opponentId !== null ? botById.get(opponentId) : undefined;
            myAction = (
                <div className="flex flex-col items-center gap-2 w-full">
                <button
                    className="w-full sm:w-auto px-8 py-3 rounded-md border border-white bg-white text-gray-800 font-bold hover:bg-white/80 transition cursor-pointer flex items-center justify-center gap-2 animate-pulse"
                    onClick={() => navigate(`/chess/${GAME_MINUTES}/${GAME_BONUS}/${t.my_game_id}`)}
                >
                    <Swords size={18} /> PLAY YOUR MATCH
                </button>
                {opponent && (
                    <p className="text-sm opacity-70 flex items-center gap-1">
                        vs {opponentBot && <Bot size={14} />} {opponent.username}
                        {opponentBot && ` (${botLabel(opponentBot)})`}
                    </p>
                )}
                </div>
            );
        } else if (ended) {
            myAction = null;
        } else if (me?.eliminated) {
            myAction = <p className="opacity-70">You were eliminated. You can still follow the bracket.</p>;
        } else if (t.status === "countdown" || t.status === "between_rounds") {
            myAction = <p className="opacity-70">Stay on this page: a Play button appears when your match starts.</p>;
        } else if (t.status === "in_progress" && myMatch?.is_bye) {
            myAction = <p className="opacity-70">Bye this round: you go straight to the next round.</p>;
        } else if (t.status === "in_progress" && myMatch?.winner_id === myId && myId !== null) {
            myAction = <p className="opacity-70">You won your match! Waiting for the other matches ...</p>;
        } else if (t.status === "registration" && isOrganizer) {
            // ADDED (optional bots): "Humans only" or "With bots", chosen at Start
            const canStart = withBots || t.participant_count >= 2;
            myAction = (
                <div className="flex flex-col items-center gap-2">
                    <div className="flex text-sm rounded-md border border-white/30 overflow-hidden whitespace-nowrap">
                        {[false, true].map((choice) => (
                            <button
                                key={String(choice)}
                                onClick={() => setWithBots(choice)}
                                className={`px-3 py-1 cursor-pointer transition flex items-center gap-1 ${withBots === choice ? "bg-white/15" : "hover:bg-white/5 opacity-60"}`}
                            >
                                {choice ? <><Bot size={14} /> With bots</> : <><Users size={14} /> Humans only</>}
                            </button>
                        ))}
                    </div>
                    <button
                        className={buttonClass}
                        disabled={busy || !canStart}
                        onClick={() => act(async () => {
                            if (withBots) await fillWithBots(t.id, token);
                            return startTournament(t.id, token);
                        })}
                    >
                        Start tournament
                    </button>
                    {withBots ? (
                        <p className="text-xs opacity-50 flex items-center gap-1">
                            <Bot size={12} /> Empty places are filled with AI bots at start (4 players minimum)
                        </p>
                    ) : (
                        !canStart && <p className="text-xs opacity-50">At least 2 players are needed (or choose With bots)</p>
                    )}
                </div>
            );
        } else if (t.status === "registration") {
            myAction = <p className="opacity-70">Waiting for the organizer to start the tournament ...</p>;
        }

        return (
            <div className="flex flex-col gap-4">
                {/* Status + my next action */}
                <Card
                    icon={<Trophy size={16} />}
                    title={`TOURNAMENT #${t.id}`}
                    right={<span className="px-2 py-0.5 rounded-full border border-white/20 text-xs whitespace-nowrap">{STATUS_LABEL[cancelled ? "cancelled" : t.status] ?? t.status}</span>}
                >
                    <div className="flex flex-col items-center gap-3 p-4 text-center">
                        {t.status === "finished" && (
                            <div className="flex flex-col items-center gap-1">
                                <Crown size={36} className="text-yellow-400" />
                                <p className="text-lg font-bold">{t.winner_id === myId ? "You won the tournament!" : `${winnerName ?? "?"} wins the tournament!`}</p>
                            </div>
                        )}
                        {statusLine && <p>{statusLine}</p>}
                        {myAction}
                        {ended && (
                            <button className={buttonClass} onClick={backToList}>
                                Back to tournaments
                            </button>
                        )}
                    </div>
                </Card>

                {/* Players */}
                <Card icon={<Users size={16} />} title={`PLAYERS (${t.participant_count})`}>
                    <ul className="flex flex-wrap gap-2 p-4">
                        {t.participant_details.map((p) => (
                            <li
                                key={p.id}
                                className={`px-3 py-1 rounded-full border border-white/20 text-sm flex items-center gap-1 ${p.eliminated ? "opacity-40 line-through" : ""} ${p.id === myId ? "bg-white/10" : ""}`}
                            >
                                {p.id === t.winner_id && <Crown size={12} className="text-yellow-400" />}
                                {botById.has(p.id) && <Bot size={12} className="opacity-60" />}
                                {p.username}
                                {botById.has(p.id) && <span className="text-xs opacity-50">{botLabel(botById.get(p.id)!)}</span>}
                                {p.id === t.creator_id && <span className="text-xs opacity-50">(organizer)</span>}
                            </li>
                        ))}
                    </ul>
                </Card>

                {/* Bracket (only once the tournament has started) */}
                {t.matches.length > 0 && (
                    <Card icon={<Swords size={16} />} title="BRACKET">
                        <TournamentBracket tournament={t} myId={myId} bots={botById} />
                    </Card>
                )}
            </div>
        );
    }

    return (
        <div>
            <Header />
            {/* Same frame as the profile page */}
            <div className="w-full min-h-[calc(100vh-56px)] flex flex-col justify-center items-center py-6">
                <div className="w-[92%] md:w-[85%] xl:w-[75%] bg-black/20 backdrop-blur-xs rounded-md border border-white/50 p-4 flex flex-col gap-4">
                    {offline && <p className="text-center text-red-400">Could not reach the server. Retrying ...</p>}
                    {error && (
                        <p role="alert" className="text-center text-red-400">
                            {error}
                        </p>
                    )}
                    {loading ? (
                        <div className="flex justify-center p-6">
                            <span className="loading loading-dots loading-md" />
                        </div>
                    ) : tournament ? (
                        TournamentView({ t: tournament })
                    ) : (
                        Lobby()
                    )}
                </div>
            </div>
        </div>
    );
}
