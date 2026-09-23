import { darkTile, lightTile } from "../../App";

interface Props {
  number: number;
  image?: string;
}

export default function Tile({ number, image }: Props) {
  const color = number % 2 === 0 ? darkTile : lightTile;

  return (
    <div className="aspect-square" style={{ backgroundColor: color }}>
      <div className="test"></div>
      {image && (
        <div
          style={{ backgroundImage: `url(${image})` }}
          className="chess-piece w-full h-full bg-no-repeat bg-center bg-size-[85%_85%] hover:cursor-pointer active:cursor-grabbing"
        ></div>
      )}
    </div>
  );
}