import { useAuth } from "../AuthProvider";
import { useState } from "react";
import PreviewTile from "./TilePreview";
const horizontalAxis: string[] = ["a", "b", "c", "d", "e", "f", "g", "h"];
const verticalAxis: string[] = ["1", "2", "3", "4", "5", "6", "7", "8"];

interface Piece {
  image: string;
  x: number;
  y: number;
  id: string;
}

//Pieces rendering
const initialBoardState: Piece[] = [];

for (let i = 0; i < 8; i++) {
  initialBoardState.push({image: "src/assets/pawn_b.png", x: i, y: 6, id: "♙"});
}
for (let i = 0; i < 8; i++) {
  initialBoardState.push({image: "src/assets/pawn_w.png", x: i, y: 1, id: "♙"});
}

initialBoardState.push({ image: "src/assets/rook_b.png", x: 0, y: 7, id: "♖" });
initialBoardState.push({ image: "src/assets/rook_b.png", x: 7, y: 7, id: "♖" });
initialBoardState.push({ image: "src/assets/knight_b.png", x: 1, y: 7, id: "♘"});
initialBoardState.push({ image: "src/assets/knight_b.png", x: 6, y: 7, id: "♘"});
initialBoardState.push({ image: "src/assets/bishop_b.png", x: 2, y: 7, id: "♗"});
initialBoardState.push({ image: "src/assets/bishop_b.png", x: 5, y: 7, id: "♗"});
initialBoardState.push({ image: "src/assets/queen_b.png", x: 3, y: 7, id: "♕"});
initialBoardState.push({ image: "src/assets/king_b.png", x: 4, y: 7, id: "♔" });

initialBoardState.push({ image: "src/assets/rook_w.png", x: 0, y: 0, id: "♖" });
initialBoardState.push({ image: "src/assets/rook_w.png", x: 7, y: 0, id: "♖" });
initialBoardState.push({image:"src/assets/knight_w.png", x: 1, y: 0, id: "♘"});
initialBoardState.push({image: "src/assets/knight_w.png", x: 6, y: 0,id: "♘"});
initialBoardState.push({image: "src/assets/bishop_w.png",x: 2,y: 0,id: "♗"});
initialBoardState.push({image: "src/assets/bishop_w.png", x: 5, y: 0, id: "♗"});
initialBoardState.push({image: "src/assets/queen_w.png", x: 3, y: 0, id: "♕"});
initialBoardState.push({ image: "src/assets/king_w.png", x: 4, y: 0, id: "♔" });

interface PreviewProps{
  dark: string | null;
  light: string | null;
}

export default function ChessPreview({dark, light}: PreviewProps) {
  const [pieces] = useState<Piece[]>(initialBoardState);
  const {profil} = useAuth();
  let board = [];

  if(profil) console.log("profil loading...");

  for (let j = verticalAxis.length - 1; j >= 0; j--) {
    for (let i = 0; i < horizontalAxis.length; i++) {
      const number = i + j + 2;
      let image = undefined;
      pieces.forEach((p) => {
        if (p.x === i && p.y === j) {
          image = p.image;
        }
      });

      board.push(
        <PreviewTile key={`${j}, ${i}`} image={image} number={number} dark={dark} light={light} />,
      );
    }
  }
  return (
    <div
      id="chessboard"
      className={`relative grid grid-cols-8 grid-rows-8 w-[min(50cqw,50cqh)] h-[min(50cqw,50cqh)] aspect-square select-none rounded-xl overflow-hidden`}
      style={{
        gridTemplateColumns: "repeat(8, 1fr)",
        gridTemplateRows: "repeat(8, 1fr)",
      }}
    >
      {board}
    </div>
  );
}
