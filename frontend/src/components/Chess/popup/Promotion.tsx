interface PromotionProps {
  open: boolean;
  onClose: () => void;
  setChoice: (piece: "q" | "r" | "b" | "n") => void;
  color: string;
}

const Promotion = ({ open, onClose, setChoice, color }: PromotionProps) => {
  return (
    <div
      className={`
        fixed inset-0 z-10
        flex justify-center items-center
      bg-black/30 backdrop-blur-sm
        transition-opacity duration-300
        ${open ? "opacity-100" : "opacity-0 pointer-events-none"}`}
    >
      <div
        className={`
          w-30 md:w-25
          transition-all duration-300 ease-out
          ${open ? "opacity-100 scale-100" : "opacity-0 scale-95"}`}
      >
        <div
          onClick={() => {
            setChoice("r");
            onClose();
          }}
          className="max-h-[80vh] flex flex-col justify-center items-center p-2"
        >
          <div className="w-full">
            <img
              onClick={() => {
                setChoice("q");
                onClose();
              }}
              className="w-full max-h-22.5 sm:max-h-27.5 object-contain border border-b-0 bg-mist-800/50 rounded-t-md hover:bg-mist-400/70 hover:cursor-pointer"
              src={`/src/assets/queen_${color}.png`}
              alt=""
            />
          </div>
          <div className="w-full">
            <img
              onClick={() => {
                setChoice("n");
                onClose();
              }}
              className="w-full max-h-22.5 sm:max-h-27.5 object-contain border border-b-0 border-t-0 bg-mist-800/50 hover:bg-mist-400/70 hover:cursor-pointer"
              src={`/src/assets/knight_${color}.png`}
              alt=""
            />
          </div>
          <div className="w-full">
            <img
              onClick={() => {
                setChoice("r");
                onClose();
              }}
              className="w-full max-h-22.5 sm:max-h-27.5 object-contain border border-b-0 border-t-0 bg-mist-800/50 hover:bg-mist-400/70 hover:cursor-pointer"
              src={`/src/assets/rook_${color}.png`}
              alt=""
            />
          </div>
          <div className="w-full">
            <img
              onClick={() => {
                setChoice("b");
                onClose();
              }}
              className="w-full max-h-22.5 sm:max-h-27.5 object-contain border border-t-0 bg-mist-800/50 rounded-b-md hover:bg-mist-400/70 hover:cursor-pointer"
              src={`/src/assets/bishop_${color}.png`}
              alt=""
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Promotion;
