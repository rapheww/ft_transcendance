// Friend status of other users + "send friend request", for the Add friend buttons.
// Uses the friends routes of backend/api/friends.py (requests must be accepted).
import { useCallback, useEffect, useState } from "react";
import { API } from "../Chess/utils/api";
import { useToast } from "../Toast/toastContext";

// friend = already friends, sent = I sent a request, received = they sent me a request
export type FriendStatus = "none" | "friend" | "sent" | "received";

interface UserRef {
  id: number;
}

async function getIds(path: string, token: string): Promise<number[]> {
  const response = await fetch(`${API}/friends/${path}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!response.ok) return [];
  const list: UserRef[] = await response.json();
  return list.map((u) => u.id);
}

export function useFriendStatus(token: string) {
  const toast = useToast();
  const [statusById, setStatusById] = useState<Map<number, FriendStatus>>(new Map());
  const [busyId, setBusyId] = useState<number | null>(null);

  // Load once (and again if the token changes).
  useEffect(() => {
    if (!token) return;
    let cancelled = false;
    Promise.all([getIds("", token), getIds("requests/outgoing", token), getIds("requests/incoming", token)])
      .then(([friends, sent, received]) => {
        if (cancelled) return;
        const map = new Map<number, FriendStatus>();
        received.forEach((id) => map.set(id, "received"));
        sent.forEach((id) => map.set(id, "sent"));
        friends.forEach((id) => map.set(id, "friend"));
        setStatusById(map);
      })
      .catch(() => {
        /* no status: every button shows "Add friend", the backend still checks everything */
      });
    return () => {
      cancelled = true;
    };
  }, [token]);

  const statusOf = useCallback((id: number): FriendStatus => statusById.get(id) ?? "none", [statusById]);

  // Send a request. If they had already asked me, the backend makes us friends at once.
  const addFriend = useCallback(
    async (id: number, username: string) => {
      if (!token || busyId !== null) return;
      setBusyId(id);
      try {
        const response = await fetch(`${API}/friends/requests/${id}`, {
          method: "POST",
          headers: { Authorization: `Bearer ${token}` },
        });
        const body = await response.json().catch(() => null);
        if (!response.ok) {
          toast.error(typeof body?.detail === "string" ? body.detail : "Could not send the friend request");
          return;
        }
        const accepted = body?.status === "accepted";
        setStatusById((map) => new Map(map).set(id, accepted ? "friend" : "sent"));
        toast.success(accepted ? `You and ${username} are now friends` : `Friend request sent to ${username}`);
      } catch {
        toast.error("Could not send the friend request");
      } finally {
        setBusyId(null);
      }
    },
    [token, busyId, toast],
  );

  return { statusOf, addFriend, busyId };
}
