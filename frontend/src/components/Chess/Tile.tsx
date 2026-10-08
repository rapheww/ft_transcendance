import { useAuth } from "../AuthProvider";

interface Props {
  number: number;
  image?: string;
  id?: string;
}

export default function Tile({ number, image, id }: Props) {
  const { profil } = useAuth();
  const isDark = number % 2 === 0;
  const color = isDark ? profil.board_dark_color || "var(--dark-tile)" : profil.board_light_color || "var(--light-tile)";

  return (
    <div
      className="h-full w-full"
      data-dark={isDark}
      style={{ backgroundColor: color }}
    >
      <div className="test"></div>
      {image && (
        <div
          style={{ backgroundImage: `url(${image})` }}
          id={id}
          className="chess-piece w-full h-full bg-no-repeat bg-center bg-size-[85%_85%] hover:cursor-pointer active:cursor-grabbing"
        ></div>
      )}
    </div>
  );
}
