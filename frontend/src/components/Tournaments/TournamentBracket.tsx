import { Link } from "react-router-dom";
import { Bot, Crown, Eye } from "lucide-react";
import type { BotInfo, Tournament, TournamentMatch } from "./tournamentTypes";

// Name shown above each column: last round = Final, then Semifinals, ...
function roundName(round: number, totalRounds: number): string {
  const fromEnd = totalRounds - round;
  if (fromEnd === 0) return "FINAL";
  if (fromEnd === 1) return "SEMIFINALS";
  if (fromEnd === 2) return "QUARTERFINALS";
  return `ROUND ${round}`;
}

function PlayerLine({
  name,
  won,
  lost,
  isMe,
  bot,
}: {
  name: string;
  won: boolean;
  lost: boolean;
  isMe: boolean;
  bot?: BotInfo;
}) {
  return (
    <div
      className={`flex items-center justify-between gap-2 px-3 py-1.5 ${lost ? "opacity-40" : ""}`}
    >
      <span
        className={`truncate flex items-center gap-1 ${won ? "font-bold" : ""} ${isMe ? "underline underline-offset-4" : ""}`}
      >
        {bot && <Bot size={12} className="shrink-0 opacity-60" />}
        {name}
        {bot && (
          <span className="text-xs opacity-40 font-normal">{bot.ai_level}</span>
        )}
      </span>
      {won && <Crown size={14} className="shrink-0 text-yellow-400" />}
    </div>
  );
}

function MatchCard({
  match,
  names,
  bots,
  myId,
}: {
  match: TournamentMatch;
  names: Map<number, string>;
  bots: Map<number, BotInfo>;
  myId: number | null;
}) {
  const p1 = match.player1_id;
  const p2 = match.player2_id;
  const nameOf = (id: number | null) =>
    id === null ? "TBD" : (names.get(id) ?? `#${id}`);
  const imPlaying = myId !== null && (p1 === myId || p2 === myId);
  const live = match.status === "active" && match.game_id !== null;

  return (
    <div
      className={`w-full rounded-md border ${live ? "border-white/15" : "border-white/15"} bg-black/20 text-sm`}
    >
      <PlayerLine
        name={nameOf(p1)}
        won={match.winner_id !== null && match.winner_id === p1}
        lost={match.winner_id !== null && match.winner_id !== p1}
        isMe={p1 !== null && p1 === myId}
        bot={p1 !== null ? bots.get(p1) : undefined}
      />
      <div className="border-t border-white/10" />
      {match.is_bye ? (
        // A bye: this player goes to the next round without playing
        <div className="px-3 py-1.5 text-xs opacity-40 italic">
          bye (goes through)
        </div>
      ) : (
        <PlayerLine
          name={nameOf(p2)}
          won={match.winner_id !== null && match.winner_id === p2}
          lost={match.winner_id !== null && match.winner_id !== p2}
          isMe={p2 !== null && p2 === myId}
          bot={p2 !== null ? bots.get(p2) : undefined}
        />
      )}
      {live && (
        <div className="flex items-center justify-between gap-2 px-3 py-1 border-t border-white/10 text-xs">
          <span className="flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />{" "}
            Live
          </span>
          {/* Your own match is opened with the big Play button; others can be watched */}
          {!imPlaying && (
            <Link
              to={`/watch/${match.game_id}`}
              className="flex items-center gap-1 opacity-70 hover:opacity-100"
            >
              <Eye size={12} /> Watch
            </Link>
          )}
        </div>
      )}
    </div>
  );
}

// Knockout bracket: one column per round, matches stacked in slot order.
export default function TournamentBracket({
  tournament,
  myId,
  bots = new Map(),
}: {
  tournament: Tournament;
  myId: number | null;
  bots?: Map<number, BotInfo>;
}) {
  const names = new Map(
    tournament.participant_details.map((p) => [p.id, p.username]),
  );
  const totalRounds = Math.max(0, ...tournament.matches.map((m) => m.round));
  const rounds = Array.from({ length: totalRounds }, (_, i) => i + 1);

  if (totalRounds === 0) {
    return (
      <p className="p-4 text-center opacity-60">
        The bracket appears when the tournament starts ...
      </p>
    );
  }

  return (
    // Horizontal scroll on small screens instead of squeezing the columns
    <div className="flex gap-4 overflow-x-auto p-4">
      {rounds.map((round) => {
        const matches = tournament.matches
          .filter((m) => m.round === round)
          .sort((a, b) => a.slot - b.slot);
        const current =
          round === tournament.current_round &&
          tournament.status === "in_progress";
        return (
          <div key={round} className="min-w-44 flex-1 flex flex-col">
            <p
              className={`text-xs font-bold text-center mb-3 ${current ? "" : "opacity-50"}`}
            >
              {roundName(round, totalRounds)}
              {current && " · NOW"}
            </p>
            <div className="flex-1 flex flex-col justify-around gap-3">
              {matches.map((m) => (
                <MatchCard
                  key={`${m.round}-${m.slot}`}
                  match={m}
                  names={names}
                  bots={bots}
                  myId={myId}
                />
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}
