
  interface Props {
    number: number;
    image?: string;
    id?: string;
  }

  export default function Tile({ number, image, id }: Props) {
    const color = number % 2 === 0 ? "var(--dark-tile)" : "var(--light-tile)";

    return (
      <div className="h-full w-full" style={{ backgroundColor: color }} id={color}>
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