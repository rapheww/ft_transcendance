import type React from "react";
import Tile from "./Tile";
import { useEffect, useRef, useState } from "react";
import {
  getColor,
  getTileElement,
  horizontalAxis,
  names,
  resetPiece,
  squareToPos,
  verticalAxis,
  type LastPick,
  type Movements,
  type PromoParams,
} from "../utils/utils";
import { Chess, KING, type Square } from "chess.js";
import GameOver from "../popup/GameOver";
import { useAuth } from "../../AuthProvider";
import Promotion from "../popup/Promotion";
import type { Moves } from "../Chess";
import { gameOverScreen, moveAnimation } from "../utils/animation";

export interface ChessboardProps {
  setMoves: React.Dispatch<React.SetStateAction<Moves[]>>;
  setBBonus: React.Dispatch<React.SetStateAction<boolean>>;
  setWBonus: React.Dispatch<React.SetStateAction<boolean>>;
  playerColor: string;
  canPlay: boolean;
  sendSocketMove: (move: {
    type: "move";
    from: string;
    to: string;
    promotion?: string;
  }) => boolean;
  gameId: number;
  fenInit: string;
  gameOver: boolean;
  result: string;
  setGameOver: React.Dispatch<React.SetStateAction<boolean>>;
  setResult: React.Dispatch<React.SetStateAction<string>>;
}

export default function Chessboard({
  setMoves,
  setBBonus,
  setWBonus,
  playerColor,
  canPlay,
  sendSocketMove,
  setGameOver,
  setResult,
  gameId,
  fenInit,
  gameOver,
  result,
}: ChessboardProps) {
  const chessRef = useRef(new Chess(fenInit));
  const checkedKing: string | null = chessRef.current.isCheck()
    ? (chessRef.current.findPiece({
        type: KING,
        color: chessRef.current.turn(),
      })[0] ?? null)
    : null;

  const { token, profil } = useAuth();

  const [activePiece, setActivePiece] = useState<HTMLElement | null>(null);
  const [gridX, setGridX] = useState(0);
  const [gridY, setGridY] = useState(0);
  const [fen, setFen] = useState<string>(chessRef.current.fen());
  const [tileColor, setTileColor] = useState<Movements[]>([]);
  const [lastPick, setLastPick] = useState<LastPick | null>(null);
  const [moveTile, setMoveTile] = useState<HTMLElement[]>([]);
  const [circles, setCircles] = useState<
    { svg: SVGSVGElement; tile: Square }[]
  >([]);
  const [arrows, setArrows] = useState<
    { fromx: number; fromy: number; tox: number | null; toy: number | null }[]
  >([]);
  const [currentFen, setCurrentFen] = useState<string | null>(null);
  const [open, setOpen] = useState<boolean>(false);
  const [promoOpen, setPromoOpen] = useState<boolean>(false);
  const [pendingPromo, setPendinPromo] = useState<{
    from: Square;
    to: Square;
    color: "b" | "w";
  } | null>(null);
  const [params, setParams] = useState<PromoParams | null>(null);

  //tmp arrow
  const [from, setFrom] = useState<{ x: number; y: number } | null>(null);
  const [draw, setDraw] = useState<boolean>(false);

  const lastMove = useRef<{ from: string; to: string } | null>(null);
  let newPos: string = "";
  let oldPos: string = "";
  let possible: string[] | null = null;
  //moving animation
  moveAnimation(fen, lastMove);

  //useEffect pour charger le fen quand un mouv est clique
  useEffect(() => {
    if (!fenInit) return;
    if (!currentFen) setCurrentFen(chessRef.current.fen());
    chessRef.current.load(fenInit);
    setFen(fenInit);
  }, [fenInit]);

  //gameOver
  gameOverScreen(gameId, token, setResult, setOpen, gameOver);

  function removeDot() {
    for (let i = 0; i < moveTile.length; i++) {
      if (moveTile[i]) {
        moveTile[i].style.backgroundImage = "";
        moveTile[i].style.cursor = "";
        moveTile[i].style.boxShadow = "";
      }
    }
    setMoveTile([]);
  }

  function cancelMove() {
    if (activePiece) {
      const back = activePiece.parentNode as HTMLElement;
      resetPiece(activePiece);
      setActivePiece(null);
      setTileColor((prev) => {
        const entry = prev.find((m) => m.tile === back);
        if (entry) {
          entry.tile.style.backgroundColor = entry.bg;
          return prev.filter((m) => m.tile !== back);
        }
        return prev;
      });
    }
  }

  //show dot or selected tile if ennemi piece
  function possibleMoves(possible: string[]) {
    const currentTurn = chessRef.current.turn();

    for (let i = 0; i < possible.length; i++) {
      const { x, y } = squareToPos(possible[i]);
      const tile = getTileElement(x, y);
      const possiblePiece = chessRef.current.get(possible[i] as Square);
      if (tile) {
        if (possiblePiece && possiblePiece.color != currentTurn) {
          tile.style.backgroundColor =
            tile.dataset.dark === "true"
              ? profil.board_dark_color
              : profil.board_light_color;
          tile.style.backgroundImage = `radial-gradient(transparent 0%, transparent 79%, rgba(80, 138, 82, 1) 80%)`;
        } else
          tile.style.backgroundImage =
            "radial-gradient(circle, rgba(0,0,0,0.2) 20%, transparent 21%)";
        tile.style.cursor = "pointer";
        setMoveTile((prev) => {
          const newMoveTile = [...prev];
          newMoveTile.push(tile);
          return newMoveTile;
        });
      }
    }
  }

  async function sendMove(move: string): Promise<boolean> {
    if (!token || !canPlay) return false;

    return sendSocketMove({
      type: "move",
      from: move.slice(0, 2),
      to: move.slice(2, 4),
      ...(move.length > 4 ? { promotion: move[4] } : {}),
    });
  }

  function afterMove(played: string) {
    setMoves((prev) => {
      const tmp = [...prev];
      tmp.push({ move: played, fen: chessRef.current.fen() });
      return tmp;
    });
    setLastPick(null);
    setFen(chessRef.current.fen());
    setPendinPromo(null);
    setParams(null);

    const turn = chessRef.current.turn();
    setBBonus(turn === "w");
    setWBonus(turn === "b");
    if (chessRef.current.isGameOver()) {
      setGameOver(true);
      setOpen(true);
    }
  }

  function getCoords(e: React.MouseEvent) {
    const rect = document.getElementById("chessboard")!.getBoundingClientRect();
    const tileSize = rect.width / 8;
    return {
      rect,
      tileSize,
      x: Math.floor((e.clientX - rect.left) / tileSize),
      y: 7 - Math.floor((e.clientY - rect.top) / tileSize),
    };
  }

  function setBgColor(
    target: { x: number; y: number } | undefined,
    x: number,
    y: number,
    chessboard: HTMLElement,
    active: HTMLElement | null,
  ) {
    lastMove.current = target ? { from: `${oldPos}`, to: `${newPos}` } : null;
    if (x !== gridX || y !== gridY) {
      const originTile = tileColor.find(
        (m) => m.tile === (active!.parentNode as HTMLElement),
      );
      const dest = chessboard.children[(7 - y) * 8 + x] as HTMLElement;
      const destExisting = tileColor.find((m) => m.tile === dest);
      const destColor = destExisting ? destExisting.bg : getColor(dest);

      tileColor.forEach((m) => {
        if (m.tile !== originTile?.tile && m.tile !== dest) {
          m.tile.style.backgroundColor = m.bg;
        }
      });

      if (originTile && destColor) {
        if (originTile && destColor) {
          originTile.tile.style.backgroundColor =
            originTile.tile.dataset.dark === "true" ? "#738a38" : "#97b54a";
          dest.style.backgroundColor =
            dest.dataset.dark === "true" ? "#738a38" : "#97b54a";
          setTileColor([originTile, { bg: destColor, tile: dest }]);
        }
      }
    }
  }

  function setStyle(element: HTMLElement, e: React.MouseEvent) {
    const { tileSize } = getCoords(e);
    const parentRect = (
      element.parentNode as HTMLElement
    ).getBoundingClientRect();
    Object.assign(element.style, {
      width: `${tileSize}px`,
      height: `${tileSize}px`,
      position: "absolute",
      left: `${e.clientX - parentRect.left - tileSize / 2}px`,
      top: `${e.clientY - parentRect.top - tileSize / 2}px`,
      zIndex: "50",
    });
  }

  function removeCircles() {
    circles.map((c) => {
      c.svg.style.visibility = "hidden";
    });
    setCircles([]);
  }

  function showCircle(e: React.MouseEvent){
    if (lastPick) {
        resetPiece(lastPick.piece);
        const back = lastPick.piece.parentNode as HTMLElement;
        back.style.backgroundColor = lastPick.bg;
      }
      removeDot();
      setDraw(true);
      const { x, y } = getCoords(e);
      console.log(x, y);
      setFrom({ x: x, y: 7 - y });
      setArrows((prev) => [
        ...prev,
        { fromx: x, fromy: y, tox: null, toy: null },
      ]);
      let tile = e.target as HTMLElement;
      if(tile.className.indexOf("chess-piece") != -1)
          tile = tile.parentNode as HTMLElement;
      if (!tile) return;
      const svg = tile.querySelector<SVGSVGElement>("svg.circle");
      if (!svg) return;
      svg.style.visibility =
        svg.style.visibility === "hidden" ? "visible" : "hidden";
      circles.push({
        svg: svg,
        tile: `${horizontalAxis[x]}${verticalAxis[y]}` as Square,
      });
  }

  function grabPiece(e: React.MouseEvent) {
    if (gameOver || !canPlay) return;

    //enlever les cercles
    if (e.button != 2) {
      setArrows([]);
      removeCircles();
    }

    //arrow
    if (e.button === 2) {
      showCircle(e);
      return;
    }

    //set current fen visible
    if (currentFen) {
      chessRef.current.load(currentFen);
      setCurrentFen("");
    }

    const chessboard = document.getElementById("chessboard");
    if (!chessboard) return;

    //drop if clicked
    const { x, y } = getCoords(e);
    const clicked = getTileElement(x, y);
    if (clicked && moveTile.includes(clicked)) {
      const selected = getTileElement(gridX, gridY)?.querySelector(
        ".chess-piece",
      ) as HTMLElement | null;
      if (selected) {
        dropPiece(null, { x, y }, selected);
        return;
      }
    }

    const element = e.target as HTMLElement;
    if (!element.classList.contains("chess-piece")) return;
    const piece = chessRef.current.get(
      `${horizontalAxis[x]}${verticalAxis[y]}` as Square,
    );
    if (!piece || piece.color !== (playerColor === "white" ? "w" : "b")) return;
    const back = element.parentNode as HTMLElement;
    if (!back) return;

    setGridX(x);
    setGridY(y);

    setStyle(element, e);
    setActivePiece(element);
    removeDot();
    if (!lastPick) {
      setLastPick({ piece: element, bg: back.style.backgroundColor });
    } else {
      if (element != lastPick.piece) {
        const old = lastPick.piece.parentNode as HTMLElement;
        if (old) {
          old.style.backgroundColor = lastPick.bg;
          setLastPick({ piece: element, bg: back.style.backgroundColor });
        }
      }
    }

    // Si la case est déjà suivie (ex: faisait partie du dernier mouvement), on réutilise sa vraie couleur
    const existing = tileColor.find((m) => m.tile === back);
    const tmpColor = existing ? existing.bg : getColor(back);
    if (!tmpColor) return;

    setTileColor((prev) =>
      existing ? prev : [...prev, { bg: tmpColor, tile: back }],
    );
    back.style.backgroundColor = "var(--select-tile)";

    const square = `${horizontalAxis[x]}${verticalAxis[y]}` as Square;
    possible = chessRef.current
      .moves({ square: square, verbose: true })
      .map((m) => m.to);
    possibleMoves(possible);
  }

  function movePiece(e: React.MouseEvent) {
    if (from != null && draw) {
      const { x, y } = getCoords(e);
      if (x != from.x || 7 - y != from.y) {
        setArrows((prev) => {
          const tmp = prev.slice(0, prev.length - 1);
          return [...tmp, { fromx: from.x, fromy: from.y, tox: x, toy: 7 - y }];
        });
        const fromCircle = getTileElement(from.x, 7 - from.y)
        if (!fromCircle) return;
        const svg = fromCircle.querySelector<SVGSVGElement>("svg.circle");
        if (!svg) return;
        svg.style.visibility = "hidden"
        const tmp = circles.filter((c) => c.tile != `${horizontalAxis[from.x]}${verticalAxis[7 - from.y]}` as Square)
        setCircles(tmp);
      } else {
        setArrows((prev) => {
          const tmp = prev.slice(0, prev.length - 1);
          return [
            ...tmp,
            { fromx: from.x, fromy: from.y, tox: null, toy: null },
          ];
        });
        const svg = getTileElement(from.x, 7 - from.y)?.querySelector<SVGSVGElement>("svg.circle");
        if (!svg) return;
        svg.style.visibility = "visible";
        circles.push({svg: svg, tile: `${horizontalAxis[x]}${verticalAxis[7 - y]}` as Square});
      }
    } else if (activePiece && activePiece.classList.contains("chess-piece")) {
      const chessboard = document.getElementById("chessboard");
      if (!chessboard) return;
      setStyle(activePiece, e);
    }
  }

  //PROMO
  async function promotion(choice: "q" | "r" | "b" | "n") {
    if (!pendingPromo || !params) return;

    const played = chessRef.current.move({
      from: pendingPromo.from,
      to: pendingPromo.to,
      promotion: choice,
    }).san;

    const sent = await sendMove(pendingPromo.from + pendingPromo.to + choice);
    if (!sent) {
      chessRef.current.undo();
      setFen(chessRef.current.fen());
      if (params.active) resetPiece(params.active);
      setActivePiece(null);
      removeDot();
      setPromoOpen(false);
      setPendinPromo(null);
      setParams(null);
      return;
    }

    setBgColor(
      params.target,
      params.x,
      params.y,
      params.chessboard,
      params.active,
    );
    afterMove(played);
  }

  async function dropPiece(
    e: React.MouseEvent | null,
    target?: { x: number; y: number },
    piece?: HTMLElement,
  ) {
    const active = piece ?? activePiece;
    if (gameOver || !canPlay) return;

    if (e?.button == 2 && from && from) {
      const { x, y } = getCoords(e);
      console.log(x, y);
      setDraw(false);
      if (x != from.x || 7 - y != from.y) {
        setArrows((prev) => {
          const tmp = prev.slice(0, prev.length - 1);
          return [...tmp, { fromx: from.x, fromy: from.y, tox: x, toy: 7 - y }];
        });
      }
    }

    if (active && (e || target)) {
      let played: string;
      const chessboard = document.getElementById("chessboard");
      if (!chessboard) return;
      const { x, y } = target ?? getCoords(e!);

      if (x < 0 || x > 7 || y < 0 || y > 7) {
        cancelMove();
        return;
      }

      //TOUTE LES MODIFS LA
      //verif du mouv
      newPos = `${horizontalAxis[x]}${verticalAxis[y]}`;
      oldPos = `${horizontalAxis[gridX]}${verticalAxis[gridY]}`;
      try {
        if (newPos == oldPos) throw "invalid";

        const piece = chessRef.current.get(oldPos as Square);

        //promo
        if (piece?.type === "p" && (newPos[1] === "8" || newPos[1] === "1")) {
          setPendinPromo({
            from: oldPos as Square,
            to: newPos as Square,
            color: piece?.color,
          });

          setParams({
            target: target,
            x: x,
            y: y,
            chessboard: chessboard,
            active: active,
          });

          setPromoOpen(true);
          resetPiece(active);
          removeDot();
          setActivePiece(null);
          return;
        }

        //normal move
        else {
          const moveNow = chessRef.current.move({
            from: `${oldPos}`,
            to: `${newPos}`,
          });
          played = moveNow.san;
          const sent = await sendMove(oldPos + newPos);
          if (!sent) {
            chessRef.current.undo();
            setFen(chessRef.current.fen());
            resetPiece(active);
            setActivePiece(null);
            removeDot();
            return;
          }
        }
      } catch {
        resetPiece(active);
        setActivePiece(null);
        return;
      }

      setBgColor(target, x, y, chessboard, active);
      resetPiece(active);
      removeDot();
      setActivePiece(null);
      //show movements
      afterMove(played);
    }
  }

  //render du board
  const grid = chessRef.current.board();

  const board = [];
  for (let j = 7; j >= 0; j--) {
    for (let i = 0; i < 8; i++) {
      const p = grid[7 - j][i];
      const image = p
        ? `/src/assets/${names[p.type]}_${p.color}.png`
        : undefined;
      const square = `${horizontalAxis[i]}${verticalAxis[j]}`;
      board.push(
        <Tile
          key={`${j}, ${i}`}
          image={image}
          number={i + j + 2}
          gameOver={gameOver}
          inCheck={square === checkedKing}
        />,
      );
    }
  }

  //arrow render
  const allsvg: React.ReactElement[] = [];
  arrows.map((a, i) => {
    if (a.tox == null || a.toy == null) return;
    const hypo = Math.hypot(a.tox - a.fromx, a.toy - a.fromy);
    allsvg.push(
      <svg
        viewBox="0 0 8 8"
        className="absolute inset-0 w-full h-full pointer-events-none z-20"
      >
        <defs>
          <marker
            id={`triangle${i}`}
            viewBox="0 0 10 10"
            refX={0.1}
            refY={5}
            markerWidth={3.2}
            markerHeight={3.2}
            markerUnits="strokeWidth"
            orient="auto"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(80, 138, 82, 0.8)" />
          </marker>
        </defs>
        <line
          x1={a.fromx + 0.5}
          y1={a.fromy + 0.5}
          x2={a.tox + 0.5 - ((a.tox - a.fromx) / hypo) * (3.2 * 0.12)}
          y2={a.toy + 0.5 - ((a.toy - a.fromy) / hypo) * (3.2 * 0.12)}
          stroke="rgba(80, 138, 82, 0.8)"
          strokeWidth="0.12"
          markerEnd={`url(#triangle${i})`}
        />
      </svg>,
    );
  });
  return (
    <div
      onMouseMove={(e) => movePiece(e)}
      onMouseDown={(e) => grabPiece(e)}
      onMouseUp={(e) => dropPiece(e)}
      onMouseLeave={cancelMove}
      onContextMenu={(e) => e.preventDefault()}
      id="chessboard"
      className={`relative bg-black grid grid-cols-8 grid-rows-8 w-[min(100cqw,100cqh)] h-[min(100cqw,100cqh)] aspect-square select-none rounded-xl overflow-hidden border-2 border-black shadow-[0_0_30px_#000000]`}
      style={{
        gridTemplateColumns: "repeat(8, 1fr)",
        gridTemplateRows: "repeat(8, 1fr)",
      }}
    >
      {board}
      {allsvg}
      <GameOver open={open} onClose={() => setOpen(false)} result={result} />
      <Promotion
        open={promoOpen}
        onClose={() => setPromoOpen(false)}
        setChoice={promotion}
        color={pendingPromo?.color as string}
      />
    </div>
  );
}