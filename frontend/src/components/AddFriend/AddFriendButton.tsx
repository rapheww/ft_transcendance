// "Add friend" button for a human player. Shows the current state instead when needed.
import { Clock, UserCheck, UserPlus } from "lucide-react";
import type { FriendStatus } from "./useFriendStatus";

interface Props {
  username: string;
  status: FriendStatus;
  busy: boolean;
  onAdd: () => void;
  compact?: boolean; // small icon-only version (tournament player chips)
}

// Same width for every state, so the Elo badges on the left stay aligned.
const SLOT = "w-28 shrink-0 flex items-center justify-start";

export function AddFriendButton(props: Props) {
  if (props.compact) return <FriendState {...props} />;
  return (
    <div className={SLOT}>
      <FriendState {...props} />
    </div>
  );
}

function FriendState({ username, status, busy, onAdd, compact = false }: Props) {
  const size = compact ? 13 : 15;

  if (status === "friend") {
    return (
      <span title={`${username} is your friend`} className={`flex items-center gap-1 text-xs opacity-60 whitespace-nowrap ${compact ? "" : "px-3"}`}>
        <UserCheck size={size} />
        {!compact && "Friends"}
      </span>
    );
  }
  if (status === "sent") {
    return (
      <span title="Friend request sent" className={`flex items-center gap-1 text-xs opacity-50 whitespace-nowrap ${compact ? "" : "px-3"}`}>
        <Clock size={size} />
        {!compact && "Requested"}
      </span>
    );
  }

  const label = status === "received" ? `Accept ${username}'s friend request` : `Add ${username} as friend`;
  return (
    <button
      type="button"
      title={label}
      aria-label={label}
      disabled={busy}
      onClick={(event) => {
        event.stopPropagation();
        onAdd();
      }}
      className={
        compact
          ? "ml-1 p-0.5 rounded-full hover:bg-white hover:text-gray-700 transition duration-350 cursor-pointer disabled:opacity-40"
          : "flex items-center gap-1 px-3 py-1 text-sm rounded-md border border-white/30 hover:bg-white hover:text-gray-700 transition duration-350 cursor-pointer disabled:opacity-40 whitespace-nowrap"
      }
    >
      <UserPlus size={size} />
      {!compact && (status === "received" ? "Accept" : "Add friend")}
    </button>
  );
}
