import type React from "react";
import Tile from "./Tile";
import { useRef, useState } from "react";
const horizontalAxis: string[] = ["a", "b", "c", "d", "e", "f", "g", "h"];
const verticalAxis: string[] = ["1", "2", "3", "4", "5", "6", "7", "8"];
import { Chess, type Square } from 'chess.js';

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
initialBoardState.push({image:"src/assets/knight_w.png", x: 1, y: 0, id: "♘"});
initialBoardState.push({image: "src/assets/knight_w.png", x: 6, y: 0,id: "♘"});
initialBoardState.push({image: "src/assets/bishop_w.png",x: 2,y: 0,id: "♗"});
initialBoardState.push({image: "src/assets/bishop_w.png", x: 5, y: 0, id: "♗"});
initialBoardState.push({image: "src/assets/queen_w.png", x: 3, y: 0, id: "♕"});
initialBoardState.push({ image: "src/assets/king_w.png", x: 4, y: 0, id: "♔" });

//get current tile color
function getColor(back: HTMLElement): string | null {
  const color = back.style.backgroundColor;
  return color;
}

interface ChessboardProps {
  setMoves: React.Dispatch<React.SetStateAction<string[]>>;
}

function getTileElement(x: number, y: number) : HTMLElement | null{
  const chessboard = document.getElementById("chessboard");
  if(!chessboard) return null;
  const index = (7 - y) * 8 + x;
  return chessboard.children[index] as HTMLElement;
}

function squareToPos(square: string){
  if(square.length > 2)
      square = square.substring(1);
  const x = horizontalAxis.indexOf(square[0]);
  const y = verticalAxis.indexOf(square[1]);
  return {x, y};
}

export default function Chessboard({ setMoves }: ChessboardProps) {
  const [activePiece, setActivePiece] = useState<HTMLElement | null>(null);
  const [gridX, setGridX] = useState(0);
  const [gridY, setGridY] = useState(0);
  const [pieces, setPieces] = useState<Piece[]>(initialBoardState);
  const [tileColor, setTileColor] = useState<Movements[]>([]);
  const [lastPick, setLastPick] = useState<LastPick | null>(null);
  const [moveTile, setMoveTile] = useState<HTMLElement[]>([]);
  let newPos: string = "";
  let oldPos :string = "";
  const chessRef = useRef(new Chess());
  let possible : string[] | null = null;

  function removeDot(){
    for(let i = 0; i < moveTile.length; i++){
      if(moveTile[i]){
        moveTile[i].style.backgroundImage = "";
      }
    }
    setMoveTile([]);
  }

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

  function possibleMoves(possible: string[]){
    for(let i = 0; i < possible.length; i++){
      const {x, y} = squareToPos(possible[i]);
      const tile = getTileElement(x, y);
      if(tile){
        tile.style.backgroundImage = "radial-gradient(circle, rgba(0,0,0,0.2) 20%, transparent 21%)";
        setMoveTile((prev) => {
          let newMoveTile = [...prev];
          newMoveTile.push(tile);
          return newMoveTile;
        })
      }
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

    const x = Math.floor((e.clientX - rect.left) / tileSize);
    const y = 7 - Math.floor((e.clientY - rect.top) / tileSize); 
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
    possible  = chessRef.current.moves({square: square});
    possibleMoves(possible);
    console.log(possible);
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

      //verif du mouv
      newPos = `${horizontalAxis[x]}${verticalAxis[y]}`;
      oldPos =`${horizontalAxis[gridX]}${verticalAxis[gridY]}`
      try{
        chessRef.current.move({ from: `${oldPos}`, to: `${newPos}` });
      }
      catch{
        resetPiece(activePiece);
        setActivePiece(null);
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

          if (origineColor === "var(--dark-tile)")
            originTile.tile.style.backgroundColor = "#738a38";
          else
            originTile.tile.style.backgroundColor = "#97b54a";

          if (dest.style.backgroundColor === "var(--dark-tile)")
            dest.style.backgroundColor = "#738a38";
          else 
            dest.style.backgroundColor = "#97b54a";
          setTileColor([originTile, { bg: destColor, tile: dest }]);
        }
        //show movements
        
        setMoves((prev) => {
          let tmp = [...prev];
          tmp.push(`${activePiece.id}${newPos}`);
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
      removeDot();
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
      className={`relative bg-black grid grid-cols-8 grid-rows-8 w-[min(100cqw,100cqh)] h-[min(100cqw,100cqh)] aspect-square select-none rounded-xl overflow-hidden border-2 border-black shadow-[0_0_60px_#000000]`}
      style={{
        gridTemplateColumns: "repeat(8, 1fr)",
        gridTemplateRows: "repeat(8, 1fr)",
      }}
    >
      {board}
    </div>
  );
}
