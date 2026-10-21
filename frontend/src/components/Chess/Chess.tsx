import Header from "../Navbar/Header";
import { useEffect, useMemo, useRef, useState } from "react";
import Chessboard from "./board/Chessboard";
import { Chess as ChessEngine } from "chess.js";
import { Flag } from "lucide-react";
import Timer from "./Timer";
import { useParams } from "react-router-dom";
import ProfilePreview from "./preview/ProfilePreview";
import { useAuth } from "../AuthProvider";

export type Moves = {
  move: string;
  fen: string;
};

interface GameInfo {
  // Les identifiants peuvent être absents tant qu'un joueur attend son adversaire.
  id: number;
  white_player_id: number | null;
  black_player_id: number | null;
  status: string;
  current_fen: string;
  fen?: string;
  pgn: string;
  result: string | null;
}

interface GameSocketMessage {
  // Le champ « type » indique le genre de message et les données qu'il contient.
  type: string;
  fen?: string;
  status?: string;
  result?: string | null;
  pgn?: string;
  san?: string;
  message?: unknown;
  user_id?: number;
}

type SocketStatus =
  | "connecting"
  | "connected"
  | "reconnecting"
  | "disconnected"
  | "finished";

const MAX_RECONNECT_ATTEMPTS = 8;
const INITIAL_RECONNECT_DELAY_MS = 1000;
const MAX_RECONNECT_DELAY_MS = 10000;

interface SocketGameState {
  fen: string;
  status?: string;
  result?: string | null;
}

function getMoveHistory(pgn: string): Moves[] {
  // Lire les coups enregistrés pour remplir la liste et permettre de revoir la partie.
  const board = new ChessEngine();
  board.loadPgn(pgn);
  return board.history({ verbose: true }).map((move) => ({
    move: move.san,
    fen: move.after,
  }));
}

function appendMove(history: Moves[], move: Moves): Moves[] {
  // Après une reconnexion, le serveur peut renvoyer un coup déjà reçu pendant le chargement.
  // On vérifie donc la position obtenue pour éviter d'ajouter ce coup deux fois.
  if (history.some((entry) => entry.fen === move.fen)) return history;
  return [...history, move];
}

function readSocketGameState(stateRef: {
  current: SocketGameState | null;
}): SocketGameState | null {
  return stateRef.current;
}

function getUserIdFromToken(token: string): number | null {
  // Le champ « sub » du jeton contient l'identifiant du compte connecté.
  try {
    const payload = token.split(".")[1];
    if (!payload) return null;

    const base64 = payload.replace(/-/g, "+").replace(/_/g, "/");

    const decoded = JSON.parse(
      atob(base64.padEnd(Math.ceil(base64.length / 4) * 4, "=")),
    );

    const id = Number(decoded.sub);
    return Number.isInteger(id) && id > 0 ? id : null;
  } catch {
    return null;
  }
}

export default function Chess() {
  // « moves » contient les coups dans l'ordre. « viewIndex » indique la position affichée.
  const [showMoves, setShowMoves] = useState(true);
  const [showChat, setShowChat] = useState(false);
  const [moves, setMoves] = useState<Moves[]>([]);
  const [wBonus, setWBonus] = useState(false);
  const [bBonus, setBBonus] = useState(false);
  const [open, setOpen] = useState(false);
  const [username, setUsername] = useState("");
  const [viewIndex, setViewIndex] = useState(-1);
  // Ces références gardent la connexion active et son dernier état sans relancer l'affichage
  // à chaque message reçu.
  const socketRef = useRef<WebSocket | null>(null);
  const socketFenRef = useRef<string>("");
  const socketSnapshotReceivedRef = useRef(false);
  const socketGameStateRef = useRef<SocketGameState | null>(null);
  const gameOverRef = useRef(false);

  const movesListRef = useRef<HTMLDivElement>(null);
  const { timer, bonus, gameId } = useParams<{
    timer: string;
    bonus: string;
    gameId: string;
  }>();

  const { user, token } = useAuth();
  // Les paramètres de l'URL sont du texte : n'accepter que les durées prévues pour la partie.
  const chrono =
    timer === "1" || timer === "5" || timer === "10" ? Number(timer) : 0;
  const add = bonus === "0" || bonus === "5" ? Number(bonus) : 0;
  const id = Number(gameId);

  const [game, setGame] = useState<GameInfo | null>(null);
  const [fen, setFen] = useState("");
  const [gameOver, setGameOver] = useState(false);
  const [result, setResult] = useState("0-0");
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState("");
  const [socketStatus, setSocketStatus] = useState<SocketStatus>("connecting");
  const [socketError, setSocketError] = useState("");
  const [opponentConnected, setOpponentConnected] = useState(false);
  const [reloadRequired, setReloadRequired] = useState(false);

  // Les événements reçus plus tard par la connexion consultent cette référence pour connaître
  // l'état actuel de la partie, plutôt qu'une ancienne valeur gardée par l'affichage.
  useEffect(() => {
    gameOverRef.current = gameOver;
  }, [gameOver]);

  const userId = token ? getUserIdFromToken(token) : null;

  // Comparer l'identifiant du compte aux joueurs pour savoir avec quelle couleur il joue.
  // Une valeur vide signifie que ce compte ne participe pas à cette partie.
  const playerColor: string =
    game && userId !== null
      ? game.white_player_id === userId
        ? "white"
        : game.black_player_id === userId
          ? "black"
          : ""
      : "";

  const opponentId =
    playerColor === "white"
      ? game?.black_player_id
      : playerColor === "black"
        ? game?.white_player_id
        : null;

  const opponentName = opponentId
    ? `Player ${opponentId}`
    : "Waiting for opponent";

  // Chaque coup joué change le joueur dont le chronomètre est actif.
  const wTurn = !gameOver && moves.length % 2 === 0;
  const bTurn = !gameOver && moves.length % 2 === 1;

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
      setGameOver(false);
      setResult("0-0");
      // Oublier aussi les données reçues par WebSocket quand on ouvre une autre partie.
      socketSnapshotReceivedRef.current = false;
      socketGameStateRef.current = null;
      gameOverRef.current = false;

      if (!token) {
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
        const response = await fetch(`http://127.0.0.1:8000/api/games/${id}`, {
          headers: { Authorization: `Bearer ${token}` },
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

  // Ouvrir une connexion à la partie déjà attribuée : la création ou la recherche d'adversaire
  // se fait ailleurs, pendant la mise en relation des joueurs.
  // Le serveur envoie les changements en direct pour garder le plateau et l'historique à jour.
  useEffect(() => {
    if (!token || !Number.isInteger(id) || id <= 0) return;
    socketFenRef.current = "";
    let stopped = false;
    let terminal = gameOverRef.current;
    let reconnectTimer: ReturnType<typeof setTimeout> | undefined;
    let retryCount = 0;
    let snapshotReceived = false;
    let pendingMoves: Moves[] = [];

    // L'adresse WebSocket transporte le jeton de connexion dans son URL pour que le serveur
    // puisse vérifier qui ouvre la connexion.
    const socketUrl = `ws://127.0.0.1:8000/ws/games/${id}?token=${encodeURIComponent(token)}`;

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

      // Attendre un peu plus longtemps avant chaque nouvel essai, sans dépasser le délai maximal.
      // Cela évite de solliciter le serveur en boucle si la connexion est coupée.
      if (retryCount >= MAX_RECONNECT_ATTEMPTS) {
        setReloadRequired(true);
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

        // presence: if the snapshot or subsequent broadcasts included the
        // opponent's connection events, they'll be handled by player_joined/
        // player_left. Reset opponentConnected when receiving a fresh snapshot
        // so presence will reflect future join/leave events.
        setOpponentConnected(false);

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
        if (data.fen) {
          socketFenRef.current = data.fen;
        }
        receiveMove(data);
        return;
      }

      if (data.type === "player_joined") {
        // mark opponent as connected when we see their join event
        if (typeof data.user_id === "number" && data.user_id === opponentId) {
          setOpponentConnected(true);
        }
        return;
      }

      if (data.type === "player_left") {
        if (typeof data.user_id === "number" && data.user_id === opponentId) {
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
        terminal = true;
        gameOverRef.current = true;
        socketGameStateRef.current = {
          fen: socketFenRef.current,
          status: "finished",
          result: data.result,
        };
        setSocketStatus("finished");
        setGameOver(true);
        setResult(data.result ?? "0-0");
        setGame((current) =>
          current
            ? { ...current, status: "finished", result: data.result ?? null }
            : current,
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
        const resp = await fetch("http://127.0.0.1:8000/api/auth/refresh", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token }),
        });
        if (!resp.ok) return false;
        const data = await resp.json();
        // update stored values so the connector uses the fresh token
        const obj: any = { username: parsed.username, token: data.access_token };
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
        setReloadRequired(false);
        setSocketStatus("connected");
        setSocketError("");
        // start application-level pings so the server can reply with "pong"
        // and we exercise the routes.py ping handling.
        try {
          if (pingInterval) clearInterval(pingInterval);
          pingInterval = setInterval(() => {
            try {
              if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
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
  }, [id, token]);

  const canPlay = socketStatus === "connected" && !gameOver;

  const movePairs = useMemo(() => {
    // Afficher les coups blancs et noirs côte à côte dans la liste des coups.
    const pairs: (Moves | null)[][] = [];

    for (let i = 0; i < moves.length; i += 2) {
      pairs.push([moves[i], moves[i + 1] ?? null]);
    }

    return pairs;
  }, [moves]);

  useEffect(() => {
    // Faire défiler la liste jusqu'aux nouveaux coups reçus sans demander au joueur de le faire.
    if (movesListRef.current) {
      movesListRef.current.scrollTop = movesListRef.current.scrollHeight;
    }
  }, [moves]);

  useEffect(() => {
    if (!open) return;

    // La touche Échap ferme l'aperçu du profil. Écouter cette touche seulement pendant son ouverture.
    function escHandler(e: KeyboardEvent) {
      if (e.key === "Escape") {
        e.preventDefault();
        setOpen(false);
      }
    }

    document.addEventListener("keydown", escHandler);

    return () => {
      document.removeEventListener("keydown", escHandler);
    };
  }, [open]);

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

  async function sendResign() {
    // Enregistrer l'abandon auprès du serveur et mettre l'écran à jour après sa confirmation.
    if (!token || !game || playerColor === "") return;

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/games/${id}/resign`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
        },
      );

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

  useEffect(() => {
    // Après la réception de nouveaux coups ou de l'historique du serveur, afficher la position actuelle.
    setViewIndex(moves.length - 1);
  }, [moves.length]);

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

  useEffect(() => {
    // Afficher sur le plateau la position choisie dans la liste ou avec les flèches.
    if (viewIndex < 0 || !moves[viewIndex]) return;

    setFen(moves[viewIndex].fen);
  }, [viewIndex, moves]);

  if (loading) {
    // Afficher le chargement, l'erreur ou le refus d'accès avant les commandes de la partie.
    return (
      <div className="min-h-screen">
        <Header />
        <p className="text-center mt-10">Loading game...</p>
      </div>
    );
  }

  if (loadError || !game || !fen) {
    return (
      <div className="min-h-screen">
        <Header />
        <div className="p-6 text-center">
          <p>{loadError || "Game data is unavailable."}</p>
        </div>
      </div>
    );
  }

  if (!playerColor) {
    return (
      <div className="min-h-screen">
        <Header />
        <p className="p-6 text-center">
          Your account is not assigned to this game.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full min-h-screen">
      <Header />

      <main className="min-h-[calc(100dvh-72px)] flex items-center justify-center px-2 md:px-4">
        <div className="flex flex-col md:flex-row lg:grid lg:grid-cols-[1fr_auto_1fr] items-center md:items-stretch lg:items-center gap-2 md:gap-3 justify-center w-full max-w-470 md:h-[calc(100dvh-72px-2rem)]">
          {/* Le centre contient le plateau et les chronomètres. Le panneau latéral montre les coups ou le chat. */}
          <div className="flex flex-col h-full w-full justify-center items-center order-1 lg:col-start-2 lg:row-start-1 lg:-translate-x-20 gap-2 md:w-auto md:h-full md:max-w-[calc(100%-clamp(240px,26vw,420px)-0.75rem)] md:shrink lg:h-auto lg:max-w-none">
            <div className="flex flex-row justify-between items-center w-full h-10 shrink-0 p-3 rounded-sm bg-mist-400/10">
              <p
                onClick={() => {
                  setOpen(true);
                  setUsername(opponentName);
                }}
                className="text-lg font-semibold hover:text-gray-300 rounded-sm p-1 cursor-pointer flex items-center gap-2"
              >
                {playerColor === "white" ? (
                  <>
                    {opponentName}
                    <span
                      aria-hidden
                      title={opponentConnected ? "Opponent connected" : "Opponent disconnected"}
                      className={`w-2 h-2 rounded-full inline-block ${opponentConnected ? "bg-green-400" : "bg-gray-500"}`}
                    />
                  </>
                ) : (
                  user || "You"
                )}
              </p>

              {/* Afficher l'état de la connexion, y compris pour les outils d'assistance. */}
              <span
                role="status"
                aria-live="polite"
                title={socketError || undefined}
                className={`text-xs ${
                  socketStatus === "connected"
                    ? "text-green-400"
                    : socketStatus === "disconnected"
                      ? "text-red-400"
                      : "text-amber-300"
                }`}
              >
                {socketStatus === "connected"
                  ? "Live"
                  : socketStatus === "connecting"
                    ? "Connecting"
                    : socketStatus === "reconnecting"
                      ? "Reconnecting"
                      : socketStatus === "finished"
                        ? "Game finished"
                        : "Offline"}
              </span>

              <div
                id="timer-1"
                className={`${
                  bTurn
                    ? "bg-white/90 rounded-sm p-1 pl-2 pr-2 text-mist-700"
                    : ""
                }`}
              >
                <Timer
                  time={chrono * 60}
                  turn={bTurn}
                  bonus={add}
                  toAdd={bBonus}
                  setGameOver={setGameOver}
                />
              </div>
            </div>

            {socketStatus !== "connected" && (
              <div
                role="status"
                aria-live="polite"
                className={`w-full rounded-sm border px-2 py-1 text-center text-[11px] ${
                  socketStatus === "reconnecting" || socketStatus === "connecting"
                    ? "border-amber-500/20 bg-amber-500/5 text-amber-200"
                    : "border-gray-500/20 bg-gray-500/5 text-gray-300"
                }`}
              >
                <div className="flex items-center justify-center gap-2">
                  <span>
                    {socketStatus === "reconnecting"
                      ? "Reconnecting to the game…"
                      : socketStatus === "connecting"
                        ? "Connecting to the game…"
                        : socketStatus === "finished"
                          ? "Game finished"
                          : reloadRequired
                            ? "Connection could not be restored"
                            : "Connection lost. Showing the last synced board"}
                  </span>
                  {reloadRequired && (
                    <button
                      type="button"
                      onClick={() => window.location.reload()}
                      className="rounded-sm border border-gray-500/30 px-1.5 py-0.5 text-[10px] uppercase tracking-wide text-gray-200 transition hover:border-gray-400 hover:text-white"
                    >
                      Reload
                    </button>
                  )}
                </div>
              </div>
            )}

            {socketError && (
              <p
                role="status"
                aria-live="polite"
                className="w-full text-center text-[11px] text-gray-300"
              >
                {socketError}
              </p>
            )}

            <div className="w-full aspect-square max-h-[65dvh] md:max-h-none md:h-auto md:w-[calc(100dvh-72px-8rem)] lg:h-auto lg:w-[min(calc(100dvh-72px-8rem),calc(100vw-2*clamp(240px,26vw,420px)-14.5rem))] flex items-center justify-center @container-size">
              <Chessboard
                setMoves={setMoves}
                setBBonus={setBBonus}
                setWBonus={setWBonus}
                setGameOver={setGameOver}
                setResult={setResult}
                gameId={id}
                fenInit={fen}
                gameOver={gameOver}
                result={result}
                playerColor={playerColor}
                canPlay={canPlay}
                sendSocketMove={sendSocketMove}
              />
            </div>

            <div className="flex flex-row justify-between items-center w-full h-10 shrink-0 p-3 rounded-sm bg-mist-400/10">
              <p
                onClick={() => {
                  setOpen(true);
                  setUsername(user || "You");
                }}
                className="text-lg font-semibold hover:text-gray-300 rounded-sm p-1 cursor-pointer"
              >
                {user || "You"} ({playerColor})
              </p>

              <div
                id="timer-2"
                className={`${
                  wTurn
                    ? "bg-white/90 rounded-sm p-1 pl-2 pr-2 text-mist-700"
                    : ""
                }`}
              >
                <Timer
                  time={chrono * 60}
                  turn={wTurn}
                  bonus={add}
                  toAdd={wBonus}
                  setGameOver={setGameOver}
                />
              </div>
            </div>
          </div>

          <div
            id="mov-resume"
            className="flex order-2 shrink-0 w-full md:h-full md:max-h-[80%] md:w-[clamp(240px,26vw,520px)] lg:col-start-3 lg:row-start-1 lg:justify-self-start rounded-md shadow-[0_0_6px_#000000] bg-mist-800 items-center justify-center flex-col"
          >
            {/* Ces boutons permettent de passer de la liste des coups au chat. */}
            <div className="w-full h-[5%] min-h-10 flex items-center justify-center rounded-t-md p-2 bg-mist-900/70">
              <p
                onClick={() => {
                  setShowChat(false);
                  setShowMoves(true);
                }}
                className="text-center uppercase w-1/2 hover:bg-gray-400/20 rounded-md cursor-pointer"
              >
                movements
              </p>

              <p
                onClick={() => {
                  setShowMoves(false);
                  setShowChat(true);
                }}
                className="text-center uppercase w-1/2 hover:bg-gray-400/20 rounded-md cursor-pointer"
              >
                CHAT
              </p>
            </div>

            <div
              id="moves"
              className={`moves-list ${
                showMoves ? "flex" : "hidden"
              } flex-col w-full h-[95%] max-h-[95%]`}
            >
              <div
                ref={movesListRef}
                className="w-full h-[90%] flex flex-col overflow-y-scroll scroll-smooth"
              >
                {movePairs.map((mov, i) => (
                  <div
                    key={i}
                    className="flex flex-row w-full justify-center text-justify h-8 shrink-0"
                  >
                    <div className="flex justify-center w-[16%] bg-mist-700 h-auto">
                      {i + 1}
                    </div>

                    {/* Cette position correspond au plateau juste après le coup. */}
                    <div
                      id={`mov-white-${i}`}
                      data-fen={mov[0]?.fen}
                      onClick={() => mov[0] && setViewIndex(i * 2)}
                      className={`flex hover:bg-mist-500 cursor-pointer w-[42%] h-auto pl-2 ${
                        viewIndex === i * 2
                          ? "bg-white text-black"
                          : "bg-mist-800"
                      }`}
                    >
                      {mov[0]?.move}
                    </div>

                    <div
                      id={`mov-black-${i}`}
                      data-fen={mov[1]?.fen}
                      onClick={() => mov[1] && setViewIndex(i * 2 + 1)}
                      className={`flex w-[42%] hover:bg-mist-500 cursor-pointer h-auto pl-2 ${
                        viewIndex === i * 2 + 1
                          ? "bg-white text-black"
                          : "bg-mist-800"
                      }`}
                    >
                      {mov[1]?.move ?? ""}
                    </div>
                  </div>
                ))}
              </div>

              <div className="h-[10%] w-full flex flex-row justify-center items-center bg-mist-900/70 gap-3">
                <div className="flex justify-center items-center w-[15%] h-[60%] bg-mist-700/60 rounded-sm hover:bg-red-600/70 hover:scale-110 duration-300">
                  X
                </div>

                <button
                  type="button"
                  onClick={sendResign}
                  className="flex justify-center items-center w-[15%] h-[60%] bg-mist-700/60 rounded-sm hover:bg-red-600/50 hover:scale-110 duration-300"
                >
                  <Flag />
                </button>
              </div>
            </div>

            <div
              id="chat"
              className={`moves-list ${
                showChat ? "flex" : "hidden"
              } flex-col w-full h-[95%] max-h-[95%] overflow-y-scroll scroll-smooth`}
            >
              <div className="w-full h-[92%] flex justify-center items-center">
                <p>MESSAGE HERE</p>
              </div>

              <input
                type="text"
                placeholder="type your message here"
                className="input input-primary w-full h-[8%] min-h-10 border-black border-t-2 rounded-b-md rounded-t-none"
              />
            </div>
          </div>
        </div>

        <ProfilePreview
          onClose={() => setOpen(false)}
          open={open}
          username={username}
        />
      </main>
    </div>
  );
}
