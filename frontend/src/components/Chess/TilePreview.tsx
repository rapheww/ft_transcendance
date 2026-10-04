import { useAuth } from "../AuthProvider";

interface Props {
  number: number;
  image?: string;
  dark: string | null;
  light: string | null;
}

export default function PreviewTile({ number, image, dark, light }: Props) {
  const { profil } = useAuth();
  if(profil) console.log("profil loading...");

  const isDark = number % 2 === 0;
  const color = isDark
    ? dark || profil.board_dark_color ||"var(--dark-tile)"
    : light || profil.board_light_color  || "var(--light-tile)";
  
  return (
    <div className="h-full w-full" style={{ backgroundColor: color }}>
      <div className="test"></div>
      {image && (
        <div
          style={{ backgroundImage: `url(${image})` }}
          className="chess-piece w-full h-full bg-no-repeat bg-center bg-size-[85%_85%]"
        ></div>
      )}
    </div>
  );
}
