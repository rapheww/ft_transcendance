import type React from "react";
import Tile from "./Tile";
import { useState } from "react";
const horizontalAxis: string[] = ["a", "b", "c", "d", "e", "f", "g", "h"];
const verticalAxis: string[] = ["1", "2", "3", "4", "5", "6", "7", "8"];

interface Piece {
  image: string;
  x: number;
  y: number;
  id: string;
}

type Movements = {
  bg: string;
  tile: HTMLElement;
};

interface LastPick {
  piece: HTMLElement;
  bg: string;
}

//Pieces rendering
const initialBoardState: Piece[] = [];

for (let i = 0; i < 8; i++) {
  initialBoardState.push({
    image: "src/assets/pawn_b.png",
    x: i,
    y: 6,
    id: "♙",
  });
}
for (let i = 0; i < 8; i++) {
  initialBoardState.push({
    image: "src/assets/pawn_w.png",
    x: i,
    y: 1,
    id: "♙",
  });
}

initialBoardState.push({ image: "src/assets/rook_b.png", x: 0, y: 7, id: "♖" });
initialBoardState.push({ image: "src/assets/rook_b.png", x: 7, y: 7, id: "♖" });
initialBoardState.push({
  image: "src/assets/knight_b.png",
  x: 1,
  y: 7,
  id: "♘",
});
initialBoardState.push({
  image: "src/assets/knight_b.png",
  x: 6,
  y: 7,
  id: "♘",
});
initialBoardState.push({
  image: "src/assets/bishop_b.png",
  x: 2,
  y: 7,
  id: "♗",
});
initialBoardState.push({
  image: "src/assets/bishop_b.png",
  x: 5,
  y: 7,
  id: "♗",
});
initialBoardState.push({
  image: "src/assets/queen_b.png",
  x: 3,
  y: 7,
  id: "♕",
});
initialBoardState.push({ image: "src/assets/king_b.png", x: 4, y: 7, id: "♔" });

initialBoardState.push({ image: "src/assets/rook_w.png", x: 0, y: 0, id: "♖" });
initialBoardState.push({ image: "src/assets/rook_w.png", x: 7, y: 0, id: "♖" });
initialBoardState.push({
  image: "src/assets/knight_w.png",
  x: 1,
  y: 0,
  id: "♘",
});
initialBoardState.push({
  image: "src/assets/knight_w.png",
  x: 6,
  y: 0,
  id: "♘",
});
initialBoardState.push({
  image: "src/assets/bishop_w.png",
  x: 2,
  y: 0,
  id: "♗",
});
initialBoardState.push({
  image: "src/assets/bishop_w.png",
  x: 5,
  y: 0,
  id: "♗",
});
initialBoardState.push({
  image: "src/assets/queen_w.png",
  x: 3,
  y: 0,
  id: "♕",
});
initialBoardState.push({ image: "src/assets/king_w.png", x: 4, y: 0, id: "♔" });

//get current tile color
function getColor(back: HTMLElement): string | null {
  const color = back.style.backgroundColor;
  return color;
}

interface ChessboardProps {
  setMoves: React.Dispatch<React.SetStateAction<string[]>>;
}

export default function Chessboard({ setMoves }: ChessboardProps) {
  const [activePiece, setActivePiece] = useState<HTMLElement | null>(null);
  const [gridX, setGridX] = useState(0);
  const [gridY, setGridY] = useState(0);
  const [pieces, setPieces] = useState<Piece[]>(initialBoardState);
  const [tileColor, setTileColor] = useState<Movements[]>([]);
  const [lastPick, setLastPick] = useState<LastPick | null>(null);

  function resetPiece(piece: HTMLElement) {
    piece.style.position = "";
    piece.style.left = "";
    piece.style.top = "";
    piece.style.width = "";
    piece.style.height = "";
    piece.style.zIndex = "";
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

  function grabPiece(e: React.MouseEvent) {
    const element = e.target as HTMLElement;
    if (!element.classList.contains("chess-piece")) return;
    let back = element.parentNode as HTMLElement;
    if (!back) return;

    const chessboard = document.getElementById("chessboard");
    if (!chessboard) return;
    const rect = chessboard.getBoundingClientRect();
    const tileSize = rect.width / 8;

    setGridX(Math.floor((e.clientX - rect.left) / tileSize));
    setGridY(7 - Math.floor((e.clientY - rect.top) / tileSize));

    element.style.width = `${tileSize}px`;
    element.style.height = `${tileSize}px`;
    element.style.position = "absolute";
    element.style.left = `${e.clientX - rect.left - tileSize / 2}px`;
    element.style.top = `${e.clientY - rect.top - tileSize / 2}px`;
    element.style.zIndex = "50";
    setActivePiece(element);
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

  function dropPiece(e: React.MouseEvent) {
    if (activePiece) {
      const chessboard = document.getElementById("chessboard");
      if (!chessboard) return;
      const chessboardRect = chessboard.getBoundingClientRect();

      const tileSize = chessboardRect.width / 8;
      const x = Math.floor((e.clientX - chessboardRect.left) / tileSize);
      const y = 7 - Math.floor((e.clientY - chessboardRect.top) / tileSize);

      if (x < 0 || x > 7 || y < 0 || y > 7) {
        cancelMove();
        return;
      }

      if (x !== gridX || y !== gridY) {
        const originTile = tileColor.find(
          (m) => m.tile === (activePiece!.parentNode as HTMLElement),
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
          let origineColor: string | null = null;
          tileColor.forEach((m) => {
            if (m.tile === originTile.tile)
              if (m.bg === "var(--dark-tile)") origineColor = m.bg;
          });
          if (!origineColor) origineColor = "var(--light-tile)";
          if (origineColor === "var(--dark-tile)") {
            originTile.tile.style.backgroundColor = "#738a38";
          } else originTile.tile.style.backgroundColor = "#97b54a";
          if (dest.style.backgroundColor === "var(--dark-tile)")
            dest.style.backgroundColor = "#738a38";
          else dest.style.backgroundColor = "#97b54a";
          setTileColor([originTile, { bg: destColor, tile: dest }]);
        }

        //show movements
        setMoves((prev) => {
          let tmp = [...prev];
          tmp.push(`${activePiece.id}${horizontalAxis[x]}${verticalAxis[y]}`);
          console.log(activePiece);
          return tmp;
        });
        setLastPick(null);
      }

      setPieces((value) => {
        const pieces = value.map((p) => {
          if (p.x === gridX && p.y === gridY) {
            p.x = x;
            p.y = y;
          }
          return p;
        });
        return pieces;
      });
      resetPiece(activePiece);
      setActivePiece(null);
    }
  }

  let board = [];

  for (let j = verticalAxis.length - 1; j >= 0; j--) {
    for (let i = 0; i < horizontalAxis.length; i++) {
      const number = i + j + 2;
      let image = undefined;
      let id = undefined;
      pieces.forEach((p) => {
        if (p.x === i && p.y === j) {
          image = p.image;
          id = p.id;
        }
      });

      board.push(
        <Tile key={`${j}, ${i}`} image={image} number={number} id={id}></Tile>,
      );
    }
  }
  return (
    <div
      onMouseMove={(e) => movePiece(e)}
      onMouseDown={(e) => grabPiece(e)}
      onMouseUp={(e) => dropPiece(e)}
      onMouseLeave={cancelMove}
      id="chessboard"
      className={`relative bg-black grid grid-cols-8 grid-rows-8 w-full max-w-[min(800px,calc(100vh-140px))] aspect-square select-none rounded-xl overflow-hidden border-2 border-black shadow-[0_0_60px_#000000]`}
    >
      {board}
    </div>
  );
}
