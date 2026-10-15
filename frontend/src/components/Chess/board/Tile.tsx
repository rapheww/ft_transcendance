import { useAuth } from "../../AuthProvider";

interface Props {
  number: number;
  image?: string;
  gameOver: boolean;
  inCheck?: boolean;
}

export default function Tile({
  number,
  image,
  gameOver,
  inCheck,
}: Props) {
  const { profil } = useAuth();
  const isDark = number % 2 === 0;
  const color = isDark
    ? profil.board_dark_color || "var(--dark-tile)"
    : profil.board_light_color || "var(--light-tile)";

  return (
    <div
      className={` relative h-full w-full`}
      data-dark={isDark}
      style={{ backgroundColor: color }}
    >
      {image && (
        <div
          style={{
            backgroundImage: `url("${image}")`,
            boxShadow: inCheck
              ? "inset 0 0 30px 8px rgba(204,60,60,0.95), inset 0 0 0 1px #CC3C3C"
              : undefined,
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
          stroke="#508a52"
          strokeWidth="5"
          opacity="0.8"
        />
      </svg>
    </div>
  );
}
