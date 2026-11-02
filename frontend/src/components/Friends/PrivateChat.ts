import { useEffect, useRef, useState } from "react";
import type { Message } from "./FriendProfil";

export function usePrivateChat(chatId: number | null, token: string | null) {
  const [live, setLive] = useState<Message[]>([]);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!chatId || !token) return;
    setLive([]);

    const proto = location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(
      `${proto}://${location.host}/ws/private-chat/${chatId}?token=${encodeURIComponent(token)}`,
    );
    socketRef.current = ws;

    ws.onmessage = (event) => {
      let data;
      try {
        data = JSON.parse(event.data);
      } catch {
        return;
      }
      if (data.type !== "private_message") return;
      setLive((prev) =>
        prev.some((m) => m.id === data.id) ? prev : [...prev, data],
      );
    };

    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 15000);

    return () => {
      clearInterval(ping);
      ws.onmessage = null;
      ws.close();
      socketRef.current = null;
    };
  }, [chatId, token]);

  function send(message: string) {
    const ws = socketRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return false;
    ws.send(JSON.stringify({ type: "message", message }));
    return true;
  }

  return { live, send };
}