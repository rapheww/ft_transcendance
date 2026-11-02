import { useEffect, useRef, useState } from "react";
import {
  appendMove,
  getMoveHistory,
  getUserIdFromToken,
  INITIAL_RECONNECT_DELAY_MS,
  MAX_RECONNECT_ATTEMPTS,
  MAX_RECONNECT_DELAY_MS,
  readSocketGameState,
  type ChatMessage,
  type GameInfo,
  type GameSocketMessage,
  type Moves,
  type SocketGameState,
  type SocketStatus,
} from "./game";
import { API } from "./api";

export function useGame(
  id: number,
  token: string | null,
  spectatorMode = false,
) {
  const [moves, setMoves] = useState<Moves[]>([]);
  const [viewIndex, setViewIndex] = useState(-1);
  const [game, setGame] = useState<GameInfo | null>(null);
  const [fen, setFen] = useState("");
  const [gameOver, setGameOver] = useState(false);
  const [result, setResult] = useState("0-0");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [socketStatus, setSocketStatus] = useState<SocketStatus>("connecting");
  const [socketError, setSocketError] = useState("");
  const [opponentConnected, setOpponentConnected] = useState(false);
  const [chat, setChat] = useState<ChatMessage[]>([]);
  const [spectatorCount, setSpectatorCount] = useState(0);
  const [drawOffer, setDrawOffer] = useState<"none" | "sent" | "received">(
    "none",
  );

  const opponentId = useRef<number | null>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const socketFenRef = useRef<string>("");
  const socketSnapshotReceivedRef = useRef(false);
  const socketGameStateRef = useRef<SocketGameState | null>(null);
  const gameOverRef = useRef(false);
  const waitingForSpectatableGame =
    spectatorMode && (!game || game.status === "waiting");

  const userId = token ? getUserIdFromToken(token) : null;

  const playerColor: string =
    game && userId !== null
      ? game.white_player_id === userId
        ? "white"
        : game.black_player_id === userId
          ? "black"
          : ""
      : "";

  opponentId.current = !game
    ? null
    : playerColor === "white"
      ? game.black_player_id
      : playerColor === "black"
        ? game.white_player_id
        : null;

  const opponentName =
    (playerColor === "white"
      ? game?.black_player_name
      : playerColor === "black"
        ? game?.white_player_name
        : undefined) ??
    (opponentId.current
      ? `Player ${opponentId.current}`
      : game?.opponent_type === "ai"
        ? `AI${game.ai_difficulty ? ` (${game.ai_difficulty})` : ""}`
        : "Waiting for opponent");

  const playerName =
    playerColor === "white"
      ? game?.white_player_name
      : playerColor === "black"
        ? game?.black_player_name
        : undefined;

  useEffect(() => {
    gameOverRef.current = gameOver;
  }, [gameOver]);

  useEffect(() => {
    const controller = new AbortController();
    let cancelled = false;

    // Charger la partie enregistrée pour qu'un lien direct ou un rechargement la restaure.
    async function loadGame() {
      setLoading(true);
      setLoadError("");
      setGame(null);
      setFen("");
      setMoves([]);
      setViewIndex(-1);
      setChat([]);
      setGameOver(false);
      setResult("0-0");
      // Oublier aussi les données reçues par WebSocket quand on ouvre une autre partie.
      socketSnapshotReceivedRef.current = false;
      socketGameStateRef.current = null;
      gameOverRef.current = false;

      if (!token && !spectatorMode) {
        setLoadError("You must be signed in to load this game.");
        setLoading(false);
        return;
      }

      if (!Number.isInteger(id) || id <= 0) {
        setLoadError("The game ID is invalid.");
        setLoading(false);
        return;
      }

      try {
        const response = await fetch(`${API}/games/${id}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
          signal: controller.signal,
        });

        if (!response.ok) {
          const detail = await response.text();
          throw new Error(
            `Could not load game (${response.status})${detail ? `: ${detail}` : ""}`,
          );
        }

        const data = (await response.json()) as GameInfo;
        if (
          !data.current_fen ||
          typeof data.pgn !== "string" ||
          !Number.isInteger(data.id)
        ) {
          throw new Error("The server returned invalid game data.");
        }

        if (cancelled) return;

        // La connexion WebSocket peut répondre avant la requête de chargement.
        // Si c'est le cas, utiliser son état plus récent plutôt que les données de la requête.
        const socketState = readSocketGameState(socketGameStateRef);
        setGame(
          socketState
            ? {
                ...data,
                current_fen: socketState.fen || data.current_fen,
                status: socketState.status ?? data.status,
                result:
                  socketState.result !== undefined
                    ? socketState.result
                    : data.result,
                white_time_remaining:
                  socketState.white_time_remaining ?? data.white_time_remaining,
                black_time_remaining:
                  socketState.black_time_remaining ?? data.black_time_remaining,
                increment_seconds:
                  socketState.increment_seconds ?? data.increment_seconds,
                last_move_at: socketState.last_move_at ?? data.last_move_at,
                can_claim_fifty_move:
                  socketState.can_claim_fifty_move ?? data.can_claim_fifty_move,
                can_claim_threefold_repetition:
                  socketState.can_claim_threefold_repetition ??
                  data.can_claim_threefold_repetition,
              }
            : data,
        );
        setFen(socketState?.fen || data.current_fen);
        if (!socketSnapshotReceivedRef.current) {
          const history = getMoveHistory(data.pgn);
          setMoves(history);
          setViewIndex(history.length - 1);
        }
        setGameOver((socketState?.status ?? data.status) === "finished");
        setResult(
          (socketState?.result !== undefined
            ? socketState.result
            : data.result) ?? "0-0",
        );
      } catch (error) {
        // Une requête annulée concerne une ancienne page ou partie : ignorer sa réponse.
        if (cancelled) return;
        setLoadError(
          error instanceof Error ? error.message : "Could not load game.",
        );
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void loadGame();

    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [id, token]);

  useEffect(() => {
    if ((!token && !spectatorMode) || !Number.isInteger(id) || id <= 0) return;
    if (waitingForSpectatableGame) return;
    socketFenRef.current = "";
    let stopped = false;
    let terminal = gameOverRef.current;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
    let retryCount = 0;
    let snapshotReceived = false;
    let pendingMoves: Moves[] = [];
    let pendingChat: ChatMessage[] = [];

    function isChatMessage(value: unknown): value is ChatMessage {
      if (!value || typeof value !== "object") return false;
      const message = value as Partial<ChatMessage>;
      return (
        Number.isInteger(message.id) &&
        Number.isInteger(message.user_id) &&
        typeof message.username === "string" &&
        typeof message.message === "string"
      );
    }

    // L'adresse WebSocket transporte le jeton de connexion dans son URL pour que le serveur
    // puisse vérifier qui ouvre la connexion.
    const proto = location.protocol === "https:" ? "wss" : "ws";
    const socketUrl = token
      ? `${proto}://${location.host}/ws/games/${id}?token=${encodeURIComponent(token)}`
      : `${proto}://${location.host}/ws/games/${id}`;

    function receiveMove(data: GameSocketMessage) {
      if (typeof data.san !== "string" || typeof data.fen !== "string") return;
      const move = { move: data.san, fen: data.fen };

      // Garder les coups reçus de côté jusqu'à recevoir l'historique de départ du serveur.
      // On pourra ensuite les ajouter dans le bon ordre à cet historique.
      if (!snapshotReceived) {
        pendingMoves.push(move);
        return;
      }

      setMoves((history) => appendMove(history, move));
    }

    function scheduleReconnect() {
      if (stopped || terminal) return;

      const newLocal = retryCount >= MAX_RECONNECT_ATTEMPTS;
      if (newLocal) {
        setSocketStatus("disconnected");
        setSocketError(
          `Could not reconnect after ${MAX_RECONNECT_ATTEMPTS} attempts. Reload the page to continue.`,
        );
        return;
      }

      const delay = Math.min(
        INITIAL_RECONNECT_DELAY_MS * 2 ** retryCount,
        MAX_RECONNECT_DELAY_MS,
      );
      retryCount += 1;
      setSocketStatus("reconnecting");
      setSocketError(
        `Connection lost. Reconnecting (${retryCount}/${MAX_RECONNECT_ATTEMPTS})...`,
      );
      reconnectTimer = setTimeout(connect, delay);
    }

    function handleMessage(event: MessageEvent<string>) {
      let data: GameSocketMessage;
      try {
        data = JSON.parse(event.data) as GameSocketMessage;
      } catch {
        setSocketError("Received an invalid WebSocket message.");
        return;
      }

      if (data.type === "game_connected") {
        // À l'ouverture, le serveur envoie l'état complet de la partie, y compris après une reconnexion.
        // Cet état sert de point de départ pour afficher la partie et récupérer les changements manqués.
        retryCount = 0;
        socketGameStateRef.current = {
          fen: data.fen ?? "",
          status: data.status,
          result: data.result,
          white_time_remaining: data.white_time_remaining,
          black_time_remaining: data.black_time_remaining,
          increment_seconds: data.increment_seconds,
          last_move_at: data.last_move_at,
          can_claim_fifty_move: data.can_claim_fifty_move,
          can_claim_threefold_repetition: data.can_claim_threefold_repetition,
        };
        if (data.fen) {
          socketFenRef.current = data.fen;
          setFen(data.fen);
        }

        if (typeof data.pgn === "string") {
          try {
            // Repartir de l'historique envoyé par le serveur, puis ajouter les coups reçus entre-temps.
            // Les doublons sont ignorés si l'historique les contenait déjà.
            const history = getMoveHistory(data.pgn);
            const syncedMoves = pendingMoves.reduce(appendMove, history);
            snapshotReceived = true;
            socketSnapshotReceivedRef.current = true;
            setMoves(syncedMoves);
            setViewIndex(syncedMoves.length - 1);
            pendingMoves = [];
            setSocketError("");
          } catch {
            snapshotReceived = true;
            socketSnapshotReceivedRef.current = true;
            setSocketError(
              "Could not restore move history from the game snapshot.",
            );
            const queuedMoves = pendingMoves;
            pendingMoves = [];
            setMoves((history) => queuedMoves.reduce(appendMove, history));
          }
          const chatHistory = Array.isArray(data.chat)
            ? data.chat.filter(isChatMessage)
            : [];
          const syncedChat = new Map<number, ChatMessage>();
          [...chatHistory, ...pendingChat].forEach((message) => {
            syncedChat.set(message.id, message);
          });
          setChat([...syncedChat.values()]);
          pendingChat = [];
        } else {
          setSocketError("The server snapshot did not include move history.");
        }

        if (data.status) {
          const status = data.status;
          setGame((current) =>
            current
              ? {
                  ...current,
                  current_fen: data.fen ?? current.current_fen,
                  status,
                  result: data.result ?? current.result,
                  white_time_remaining:
                    data.white_time_remaining ?? current.white_time_remaining,
                  black_time_remaining:
                    data.black_time_remaining ?? current.black_time_remaining,
                  increment_seconds:
                    data.increment_seconds ?? current.increment_seconds,
                  last_move_at: data.last_move_at ?? current.last_move_at,
                  can_claim_fifty_move:
                    data.can_claim_fifty_move ?? current.can_claim_fifty_move,
                  can_claim_threefold_repetition:
                    data.can_claim_threefold_repetition ??
                    current.can_claim_threefold_repetition,
                }
              : current,
          );
        }
        if (
          typeof data.spectator_count === "number" &&
          Number.isInteger(data.spectator_count)
        ) {
          setSpectatorCount(data.spectator_count);
        }

        if (data.status === "finished") {
          terminal = true;
          gameOverRef.current = true;
          setSocketStatus("finished");
          setGameOver(true);
          setResult(data.result ?? "0-0");
        } else if (data.status === "active") {
          gameOverRef.current = false;
          setGameOver(false);
        }

        return;
      }

      if (data.type === "game_state") {
        // Ce message met à jour la position et le résultat éventuel, sans remplacer la liste des coups.
        const previousSocketState = socketGameStateRef.current;
        socketGameStateRef.current = {
          fen: data.fen ?? previousSocketState?.fen ?? "",
          status: data.status ?? previousSocketState?.status,
          result:
            data.result !== undefined
              ? data.result
              : previousSocketState?.result,
          white_time_remaining:
            data.white_time_remaining ??
            previousSocketState?.white_time_remaining,
          black_time_remaining:
            data.black_time_remaining ??
            previousSocketState?.black_time_remaining,
          increment_seconds:
            data.increment_seconds ?? previousSocketState?.increment_seconds,
          last_move_at: data.last_move_at ?? previousSocketState?.last_move_at,
          can_claim_fifty_move:
            data.can_claim_fifty_move ??
            previousSocketState?.can_claim_fifty_move,
          can_claim_threefold_repetition:
            data.can_claim_threefold_repetition ??
            previousSocketState?.can_claim_threefold_repetition,
        };
        if (data.fen) {
          socketFenRef.current = data.fen;
          setFen(data.fen);
        }

        if (data.status) {
          const status = data.status;
          setGame((current) =>
            current
              ? {
                  ...current,
                  current_fen: data.fen ?? current.current_fen,
                  status,
                  result: data.result ?? current.result,
                  white_time_remaining:
                    data.white_time_remaining ?? current.white_time_remaining,
                  black_time_remaining:
                    data.black_time_remaining ?? current.black_time_remaining,
                  increment_seconds:
                    data.increment_seconds ?? current.increment_seconds,
                  last_move_at: data.last_move_at ?? current.last_move_at,
                  can_claim_fifty_move:
                    data.can_claim_fifty_move ?? current.can_claim_fifty_move,
                  can_claim_threefold_repetition:
                    data.can_claim_threefold_repetition ??
                    current.can_claim_threefold_repetition,
                }
              : current,
          );
        }

        if (data.status === "finished") {
          terminal = true;
          gameOverRef.current = true;
          setSocketStatus("finished");
          setGameOver(true);
          setResult(data.result ?? "0-0");
        } else if (data.status === "active") {
          gameOverRef.current = false;
          setGameOver(false);
        }

        return;
      }

      if (data.type === "move") {
        // Le coup reçu contient son écriture pour l'afficher et la position du plateau après ce coup.
        // Le serveur l'a déjà vérifié et accepté.
        setDrawOffer("none");
        if (data.fen) {
          socketFenRef.current = data.fen;
        }
        setGame((current) =>
          current
            ? {
                ...current,
                white_time_remaining:
                  data.white_time_remaining ?? current.white_time_remaining,
                black_time_remaining:
                  data.black_time_remaining ?? current.black_time_remaining,
                increment_seconds:
                  data.increment_seconds ?? current.increment_seconds,
                last_move_at: data.last_move_at ?? current.last_move_at,
                can_claim_fifty_move:
                  data.can_claim_fifty_move ?? current.can_claim_fifty_move,
                can_claim_threefold_repetition:
                  data.can_claim_threefold_repetition ??
                  current.can_claim_threefold_repetition,
              }
            : current,
        );
        receiveMove(data);
        return;
      }
      if (data.type === "draw_offered") {
        setDrawOffer(data.user_id === userId ? "sent" : "received");
        return;
      }
      if (data.type === "draw_declined") {
        setDrawOffer("none");
        return;
      }
      if (data.type === "spectator_count") {
        if (typeof data.count === "number" && Number.isInteger(data.count)) {
          setSpectatorCount(data.count);
        }
        return;
      }

      if (data.type === "player_joined") {
        if (
          typeof data.user_id === "number" &&
          data.user_id === opponentId.current
        ) {
          setOpponentConnected(true);
        }
        return;
      }

      if (data.type === "player_left") {
        if (
          typeof data.user_id === "number" &&
          data.user_id === opponentId.current
        ) {
          setOpponentConnected(false);
        }
        return;
      }

      if (data.type === "error") {
        setSocketError(String(data.message ?? "WebSocket server error."));
        return;
      }

      if (data.type === "game_over") {
        // La partie est terminée : ne pas essayer de se reconnecter et arrêter les deux chronomètres.
        setDrawOffer("none");
        terminal = true;
        gameOverRef.current = true;
        socketGameStateRef.current = {
          fen: socketFenRef.current,
          status: "finished",
          result: data.result,
          can_claim_fifty_move: false,
          can_claim_threefold_repetition: false,
        };
        setSocketStatus("finished");
        setGameOver(true);
        setResult(data.result ?? "0-0");
        setGame((current) =>
          current
            ? {
                ...current,
                status: "finished",
                result: data.result ?? null,
                can_claim_fifty_move: false,
                can_claim_threefold_repetition: false,
              }
            : current,
        );
      }

      if (data.type === "chat") {
        if (!isChatMessage(data)) return;
        if (!snapshotReceived) {
          pendingChat.push(data);
          return;
        }
        setChat((previous) =>
          previous.some((message) => message.id === data.id)
            ? previous
            : [...previous, data],
        );
      }
    }

    async function tryRefreshToken(): Promise<boolean> {
      // Try to refresh via the REST endpoint if possible (AuthProvider stores refreshToken in localStorage)
      try {
        const stored = localStorage.getItem("user");
        if (!stored) return false;
        const parsed = JSON.parse(stored);
        const refresh_token = parsed?.refresh_token;
        if (!refresh_token) return false;
        const resp = await fetch(`${API}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token }),
        });
        if (!resp.ok) return false;
        const data = await resp.json();
        // update stored values so the connector uses the fresh token
        const obj: any = {
          username: parsed.username,
          token: data.access_token,
        };
        if (data.refresh_token) obj.refresh_token = data.refresh_token;
        localStorage.setItem("user", JSON.stringify(obj));
        return true;
      } catch {
        return false;
      }
    }

    function connect() {
      if (stopped || terminal || gameOverRef.current) {
        if (gameOverRef.current) setSocketStatus("finished");
        return;
      }

      setSocketStatus(retryCount === 0 ? "connecting" : "reconnecting");
      let ws: WebSocket;
      let pingInterval: ReturnType<typeof setInterval> | undefined;
      try {
        ws = new WebSocket(socketUrl);
      } catch {
        scheduleReconnect();
        return;
      }

      socketRef.current = ws;
      ws.onopen = () => {
        if (stopped || socketRef.current !== ws) return;
        setSocketStatus("connected");
        setSocketError("");
        // start application-level pings so the server can reply with "pong"
        // and we exercise the routes.py ping handling.
        try {
          if (pingInterval) clearInterval(pingInterval);
          pingInterval = setInterval(() => {
            try {
              if (
                socketRef.current &&
                socketRef.current.readyState === WebSocket.OPEN
              ) {
                socketRef.current.send(JSON.stringify({ type: "ping" }));
              }
            } catch {
              // ignore send errors; onerror/onclose will handle reconnects
            }
          }, 15000);
        } catch {
          // ignore interval setup failures in unusual environments
        }
      };
      ws.onclose = async (ev) => {
        // if the server closed for policy (1008), try a token refresh once
        if (ev && ev.code === 1008) {
          const refreshed = await tryRefreshToken();
          if (refreshed) {
            // attempt immediate reconnect with new token
            if (socketRef.current === ws) socketRef.current = null;
            connect();
            return;
          }
          setSocketError("Session expired. Reload this page to reconnect.");
        }
        // fallback to default close handling
        if (socketRef.current === ws) socketRef.current = null;
        scheduleReconnect();
      };
      ws.onmessage = handleMessage;
      ws.onerror = () => {
        setSocketError("WebSocket connection error.");
        ws.close();
      };
    }

    connect();

    return () => {
      // Retirer les gestionnaires avant de fermer la connexion pour que son arrêt ne déclenche
      // ni mise à jour de l'affichage ni nouvel essai de connexion.
      stopped = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      const ws = socketRef.current;
      socketRef.current = null;
      if (ws) {
        ws.onopen = null;
        ws.onmessage = null;
        ws.onerror = null;
        ws.onclose = null;
        try {
          ws.close();
        } catch {
          // ignore
        }
      }
    };
  }, [id, token, waitingForSpectatableGame]);

  useEffect(() => {
    // Après la réception de nouveaux coups ou de l'historique du serveur, afficher la position actuelle.
    setViewIndex(moves.length - 1);
  }, [moves.length]);

  useEffect(() => {
    // Afficher sur le plateau la position choisie dans la liste ou avec les flèches.
    if (viewIndex < 0 || !moves[viewIndex]) return;

    setFen(moves[viewIndex].fen);
  }, [viewIndex, moves]);

  useEffect(() => {
    // Les flèches permettent de revoir les coups, sauf quand on écrit dans un champ de texte.
    function arrowHandler(e: KeyboardEvent) {
      if (e.key !== "ArrowLeft" && e.key !== "ArrowRight") {
        return;
      }

      if (e.target instanceof HTMLInputElement) return;
      if (moves.length === 0) return;

      e.preventDefault();

      setViewIndex((index) =>
        e.key === "ArrowLeft"
          ? Math.max(index - 1, 0)
          : Math.min(index + 1, moves.length - 1),
      );
    }

    document.addEventListener("keydown", arrowHandler);

    return () => {
      document.removeEventListener("keydown", arrowHandler);
    };
  }, [moves.length]);

  // Chaque coup joué change le joueur dont le chronomètre est actif.
  const wTurn = !gameOver && moves.length % 2 === 0;
  const bTurn = !gameOver && moves.length % 2 === 1;

  const canPlay =
    playerColor !== "" && socketStatus === "connected" && !gameOver;

  function sendSocketMove(move: {
    type: "move";
    from: string;
    to: string;
    promotion?: string;
  }) {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return false;
    }

    socket.send(JSON.stringify(move));
    return true;
  }

  function sendChat(chat: { type: "chat"; message: string; username: string }) {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      return false;
    }

    socket.send(JSON.stringify(chat));
    return true;
  }

  function sendDraw(type: "draw_offer" | "draw_accept" | "draw_decline") {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) return false;
    socket.send(JSON.stringify({ type }));
    return true;
  }

  async function sendResign() {
    // Enregistrer l'abandon auprès du serveur et mettre l'écran à jour après sa confirmation.
    if (!token || !game || playerColor === "") return;

    try {
      const response = await fetch(`${API}/games/${id}/resign`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        console.error("Resign rejected:", await response.text());
        return;
      }

      const data: GameInfo = await response.json();

      setGame(data);
      setResult(data.result ?? "0-0");
      setGameOver(true);
    } catch (error) {
      console.error("Error resigning:", error);
    }
  }

  return {
    game,
    fen,
    moves,
    setMoves,
    viewIndex,
    setViewIndex,
    gameOver,
    setGameOver,
    result,
    setResult,
    loading,
    loadError,
    socketStatus,
    socketError,
    opponentConnected,
    playerColor,
    playerName,
    opponentId,
    canPlay,
    sendSocketMove,
    sendChat,
    sendResign,
    opponentName,
    wTurn,
    bTurn,
    chat,
    spectatorCount,
    drawOffer,
    sendDraw
  };
}
