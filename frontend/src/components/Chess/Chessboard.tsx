import type React from "react";
import Tile from "./Tile";
import { useEffect, useLayoutEffect, useRef, useState } from "react";
const horizontalAxis: string[] = ["a", "b", "c", "d", "e", "f", "g", "h"];
const verticalAxis: string[] = ["1", "2", "3", "4", "5", "6", "7", "8"];
import { Chess, type Square } from "chess.js";
import GameOver from "./GameOver";
import { useAuth } from "../AuthProvider";
import type { Moves } from "./Chess";

type Movements = {
  bg: string;
  tile: HTMLElement;
};

interface LastPick {
  piece: HTMLElement;
  bg: string;
}

//get current tile color
function getColor(back: HTMLElement): string | null {
  const color = back.style.backgroundColor;
  return color;
}

interface ChessboardProps {
  setMoves: React.Dispatch<React.SetStateAction<Moves[]>>;
  setBBonus: React.Dispatch<React.SetStateAction<boolean>>;
  setWBonus: React.Dispatch<React.SetStateAction<boolean>>;
  sendSocketMessage: (message: object) => boolean;
  playerColor: string;
  gameId: number;
  fenInit: string;
  gameOver: boolean;
  result: string;
  setGameOver: React.Dispatch<React.SetStateAction<boolean>>;
  setResult: React.Dispatch<React.SetStateAction<string>>;
}

function getTileElement(x: number, y: number): HTMLElement | null {
  const chessboard = document.getElementById("chessboard");
  if (!chessboard) return null;
  const index = (7 - y) * 8 + x;
  return chessboard.children[index] as HTMLElement;
}

function squareToPos(square: string) {
  if (square.length > 2) square = square.substring(1);
  const x = horizontalAxis.indexOf(square[0]);
  const y = verticalAxis.indexOf(square[1]);
  return { x, y };
}

function resetPiece(piece: HTMLElement) {
    piece.style.position = "";
    piece.style.left = "";
    piece.style.top = "";
    piece.style.width = "";
    piece.style.height = "";
    piece.style.zIndex = "";
}

export default function Chessboard({
  setMoves,
  setBBonus,
  setWBonus,
  playerColor,
  sendSocketMessage,
  setGameOver,
  setResult,
  gameId,
  fenInit,
  gameOver,
  result
}: ChessboardProps) {
  const chessRef = useRef(new Chess(fenInit));

  const { token } = useAuth();

  const [activePiece, setActivePiece] = useState<HTMLElement | null>(null);
  const [gridX, setGridX] = useState(0);
  const [gridY, setGridY] = useState(0);
  const [fen, setFen] = useState<string>(chessRef.current.fen());
  const [tileColor, setTileColor] = useState<Movements[]>([]);
  const [lastPick, setLastPick] = useState<LastPick | null>(null);
  const [moveTile, setMoveTile] = useState<HTMLElement[]>([]);
  const [currentFen, setCurrentFen] = useState<string | null>(null);
  const [open, setOpen] = useState<boolean>(false);
  const lastMove = useRef<{ from: string; to: string } | null>(null);
  let newPos: string = "";
  let oldPos: string = "";
  let possible: string[] | null = null;

  //moving animation
  useLayoutEffect(() => {
    const m = lastMove.current; //tmp to get the lastmove
    if (!m) return;
    lastMove.current = null; //set the value to null

    const from = squareToPos(m.from); //getting the from pos
    const to = squareToPos(m.to); // getting the to pos
    const tf = getTileElement(from.x, from.y); //getting the element from
    const tt = getTileElement(to.x, to.y); // getting the element to

    if (!tf || !tt) return;

    const a = tf.getBoundingClientRect(); //getting the coordonates of the element from
    const b = tt.getBoundingClientRect(); //getting the coordonates of the element to
    tt.querySelector(".chess-piece")?.animate(
      //animation of the class chess-piece
      [
        { transform: `translate(${a.left - b.left}px, ${a.top - b.top}px)` },
        { transform: "none" },
      ] /*this is this animation translate from a to b*/,
      { duration: 200, easing: "ease-out" },
    );
  }, [fen]);

  //useEffect pour charger le fen quand un mouv est clique
  useEffect(() => {
    if (!fenInit) return;
    if(!currentFen)
        setCurrentFen(chessRef.current.fen());
    chessRef.current.load(fenInit);
    setFen(fenInit);
  }, [fenInit])

  useEffect(() => {
    if(!gameOver) return;

    async function getResult(){
    try{
       const response = await fetch(`http://127.0.0.1:8000/api/games/${gameId}`,
          {headers: { Authorization: `Bearer ${token}` }}
       );
       if(!response.ok) return;
       const game = await response.json();
       if(game.status === "finished"){
         setResult(game.result);
         setOpen(true)
       }
    }
    catch{
      return;
    }
  }

  getResult();
  }, [gameOver])

  function removeDot() {
    for (let i = 0; i < moveTile.length; i++) {
      if (moveTile[i]) {
        moveTile[i].style.backgroundImage = "";
        moveTile[i].style.cursor = "";
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

  function possibleMoves(possible: string[]) {
    for (let i = 0; i < possible.length; i++) {
      const { x, y } = squareToPos(possible[i]);
      const tile = getTileElement(x, y);
      if (tile) {
        tile.style.backgroundImage =
          "radial-gradient(circle, rgba(0,0,0,0.2) 20%, transparent 21%)";
        tile.style.cursor = "pointer";
        setMoveTile((prev) => {
          let newMoveTile = [...prev];
          newMoveTile.push(tile);
          return newMoveTile;
        });
      }
    }
  }

  async function sendMove(move: string): Promise<boolean> {
  if (!token) return false;

    try {
      const response = await fetch(
        `http://127.0.0.1:8000/api/games/${gameId}/move`,
        {
          method: "POST",
          headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ move }),
        },
      );

      if (!response.ok) {
        console.error(
          "Move rejected by server:",
          await response.text(),
        );
        return false;
      }

      const infos = await response.json();

      chessRef.current.load(infos.current_fen);
      setFen(infos.current_fen);

      if (infos.status === "finished") {
        setGameOver(true);
        setResult(infos.result);
      }

      return true;
    } catch (error) {
      console.error("Error making move:", error);
      return false;
    }
  }


  function grabPiece(e: React.MouseEvent) {
    if (gameOver) return;
    //set current fen visible
    if(currentFen){
      chessRef.current.load(currentFen);
      setCurrentFen("");
    }
    const chessboard = document.getElementById("chessboard");
    if (!chessboard) return;
    const rect = chessboard.getBoundingClientRect();
    const tileSize = rect.width / 8;
    const x = Math.floor((e.clientX - rect.left) / tileSize);
    const y = 7 - Math.floor((e.clientY - rect.top) / tileSize);

    const clicked = getTileElement(x, y);
    if (clicked && moveTile.includes(clicked)) {
      // Let onMouseUp handle the move, so we don't submit it twice.
      return;
    }

    if (e.button === 2) {
      console.log("arrow");
      //arrow code
      return;
    }

    const element = e.target as HTMLElement;
    if (!element.classList.contains("chess-piece")) return;
    let back = element.parentNode as HTMLElement;
    if (!back) return;

    setGridX(x);
    setGridY(y);

    element.style.width = `${tileSize}px`;
    element.style.height = `${tileSize}px`;
    element.style.position = "absolute";
    element.style.left = `${e.clientX - rect.left - tileSize / 2}px`;
    element.style.top = `${e.clientY - rect.top - tileSize / 2}px`;
    element.style.zIndex = "50";
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
    const piece = chessRef.current.get(square);

    if (!piece || piece.color !== (playerColor === "white" ? "w" : "b")) {
      cancelMove();
      return;
    }
    possible = chessRef.current
      .moves({ square: square, verbose: true })
      .map((m) => m.to);
    possibleMoves(possible);
  }

  function movePiece(e: React.MouseEvent) {
    if (activePiece && activePiece.classList.contains("chess-piece")) {
      const chessboard = document.getElementById("chessboard");
      if (!chessboard) return;
      const chessboardRect = chessboard.getBoundingClientRect();

      const gridSize = chessboardRect.width / 8;

      activePiece.style.width = `${gridSize}px`;
      activePiece.style.height = `${gridSize}px`;

      const x = e.clientX - chessboardRect.left - gridSize / 2;
      const y = e.clientY - chessboardRect.top - gridSize / 2;

      activePiece.style.position = "absolute";
      activePiece.style.left = `${x}px`;
      activePiece.style.top = `${y}px`;
      activePiece.style.zIndex = "50";
    }
  }

  async function dropPiece(
    e: React.MouseEvent | null,
    target?: { x: number; y: number },
    piece?: HTMLElement,
  ) {
    const active = piece ?? activePiece;
    if (gameOver) return;
    if (active && (e || target)) {
      let played: string = "";
      const chessboard = document.getElementById("chessboard");
      if (!chessboard) return;
      const chessboardRect = chessboard.getBoundingClientRect();

      const tileSize = chessboardRect.width / 8;
      const x = target
        ? target.x
        : Math.floor((e!.clientX - chessboardRect.left) / tileSize);
      const y = target
        ? target.y
        : 7 - Math.floor((e!.clientY - chessboardRect.top) / tileSize);

      if (x < 0 || x > 7 || y < 0 || y > 7) {
        cancelMove();
        return;
      }

      //verif du mouv
      newPos = `${horizontalAxis[x]}${verticalAxis[y]}`;
      oldPos = `${horizontalAxis[gridX]}${verticalAxis[gridY]}`;

      try {
        if (newPos === oldPos) {
          resetPiece(active);
          setActivePiece(null);
          return;
        }

        const candidate = new Chess(chessRef.current.fen());

        played = candidate.move({
          from: oldPos,
          to: newPos
        }).san;

        const accepted = await sendMove(oldPos + newPos);

        if (!accepted) {
          resetPiece(active);
          setActivePiece(null);
          removeDot();
          return;
        }
      } catch {
        resetPiece(active);
        setActivePiece(null);
        removeDot();
        return;
      }

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

        setLastPick(null);
      }
      setFen(chessRef.current.fen());
      resetPiece(active);
      removeDot();
      setActivePiece(null);
      const turn = chessRef.current.turn();
      if (turn === "w") {
        setBBonus(true);
        setWBonus(false);
      } else {
        setWBonus(true);
        setBBonus(false);
      }
      if (chessRef.current.isGameOver()) {
        setGameOver(true);
        setOpen(true);
      }
    }
  }

  //render du board
  const grid = chessRef.current.board();
  const names = {
    p: "pawn",
    n: "knight",
    b: "bishop",
    k: "king",
    q: "queen",
    r: "rook",
  };

  let board = [];
  for (let j = 7; j >= 0; j--) {
    for (let i = 0; i < 8; i++) {
      const p = grid[7 - j][i];
      const image = p
        ? `/src/assets/${names[p.type]}_${p.color}.png`
        : undefined;
      board.push(
        <Tile
          key={`${j}, ${i}`}
          image={image}
          number={i + j + 2}
          id={p?.type}
          gameOver={gameOver}
        />,
      );
    }
  }
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
      <GameOver open={open} onClose={() => setOpen(false)} result={result} />
    </div>
  );
}
