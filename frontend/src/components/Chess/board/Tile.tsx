import { useAuth } from "../../AuthProvider";
import { horizontalAxis, verticalAxis } from "../utils/utils";

interface Props {
  number: number;
  image?: string;
  gameOver: boolean;
  inCheck?: boolean;
  tile: { x: number; y: number };
  playerColor: string;
}

export default function Tile({
  number,
  image,
  gameOver,
  inCheck,
  tile,
  playerColor,
}: Props) {
  const { profil } = useAuth();
  const isDark = number % 2 === 0;
  const color = isDark
    ? profil.board_dark_color || "var(--dark-tile)"
    : profil.board_light_color || "var(--light-tile)";

  const leftCol = playerColor === "white" ? tile.y === 0 : tile.y === 7;
  const bottomRow = playerColor === "white" ? tile.x === 0 : tile.x === 7;

  const displayCol = leftCol ? horizontalAxis[tile.x] : null;
  const displayRow = bottomRow ? verticalAxis[tile.y] : null;

  const lightColor = profil.board_light_color || "var(--light-tile)";
  const darkColor = profil.board_dark_color || "var(--dark-tile)";
  const textColor = isDark ? lightColor : darkColor;

  return (
    <div
      className={` relative h-full w-full`}
      data-dark={isDark}
      style={{ backgroundColor: inCheck ? '#ba454b' : color }}
    >
      {displayCol && (
        <p
          style={{ color: textColor }}
          className={`absolute bottom-0.5 right-0.5 text-xs lg:text-sm`}
        >
          {displayCol}
        </p>
      )}
      {displayRow && (
        <p
          style={{ color: textColor }}
          className="absolute text-black top-0.5 left-0.5 text-xs lg:text-sm"
        >
          {displayRow}
        </p>
      )}
      {image && (
        <div
          style={{
            backgroundImage: `url("${image}")`
          }}
          className={`chess-piece w-full h-full bg-no-repeat bg-center bg-size-[85%_85%] ${gameOver ? "" : "hover:cursor-pointer active:cursor-grabbing"}`}
        ></div>
      )}
      <svg
        viewBox="0 0 100 100"
        className="circle absolute inset-0 w-full h-full pointer-events-none z-10"
        style={{
          visibility: "hidden",
        }}
      >
        <circle
          cx="50"
          cy="50"
          r="42"
          fill="none"
          stroke="rgba(80, 138, 82, 0.7)"
          strokeWidth="5"
          opacity="0.8"
        />
      </svg>
    </div>
  );
}
