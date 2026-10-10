import { useCallback, useEffect, useRef, useState } from "react";

export type GameMessage = {
  type: string;
  [key: string]: unknown;
};

export function useGameSocket(gameId: number | null, token: string) {
  const socketRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<GameMessage | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!gameId || !token) return;

    const url = new URL(
      `ws://127.0.0.1:8000/ws/games/${gameId}`
    );
    url.searchParams.set("token", token);

    const socket = new WebSocket(url.toString());
    socketRef.current = socket;

    socket.onopen = () => {
      setConnected(true);
      setError(null);
    };

    socket.onmessage = (event: MessageEvent<string>) => {
      try {
        const message = JSON.parse(event.data) as GameMessage;
        setLastMessage(message);

        if (message.type === "error") {
          setError(String(message.message ?? "WebSocket error"));
        }
      } catch {
        setError("Received an invalid server message");
      }
    };

    socket.onerror = () => {
      setError("WebSocket connection error");
    };

    socket.onclose = () => {
      setConnected(false);
      if (socketRef.current === socket) {
        socketRef.current = null;
      }
    };

    return () => {
      // Prevent an old connection from affecting a newer one.
      socket.onopen = null;
      socket.onmessage = null;
      socket.onerror = null;
      socket.onclose = null;

      if (socketRef.current === socket) {
        socketRef.current = null;
      }

      socket.close();
    };
  }, [gameId, token]);

  const send = useCallback((message: object): boolean => {
    const socket = socketRef.current;

    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return false;
    }

    socket.send(JSON.stringify(message));
    return true;
  }, []);

  return { connected, lastMessage, error, send };
}