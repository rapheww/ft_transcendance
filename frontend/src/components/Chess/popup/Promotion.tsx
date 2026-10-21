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
            fixed inset-0
            flex justify-center items-center
            bg-black/30 backdrop-blur-sm
            transition-opacity duration-500 ease-out
            ${open ? "opacity-100" : "opacity-0 pointer-events-none"}
            `}
    >
      <div
        className={`
                    w-[50%] max-w-6xl
                    transition-all duration-500 ease-out
                    ${open ? "opacity-100 scale-100" : "opacity-0 scale-95"}
                    `}
      >
        <div
          onClick={() => {
            setChoice("r");
            onClose();
          }}
          className="max-h-[90vh] flex flex-col justify-center items-center p-3"
        >
          <div className="w-1/4">
            <img onClick={() => {setChoice("q");onClose();}} className="border-2 border-b-0 bg-mist-800/50 rounded-t-md hover:bg-mist-400/70" src={`/src/assets/queen_${color}.png`} alt="" />
          </div>
          <div className="w-1/4">
            <img onClick={() => {setChoice("n");onClose();}} className="border-2 border-b-0 border-t-0 bg-mist-800/50 hover:bg-mist-400/70" src={`/src/assets/knight_${color}.png`} alt="" />
          </div>
          <div className="w-1/4">
            <img onClick={() => {setChoice("r");onClose();}} className="border-2 border-b-0 border-t-0 bg-mist-800/50 hover:bg-mist-400/70" src={`/src/assets/rook_${color}.png`} alt="" />
          </div>
          <div className="w-1/4">
            <img onClick={() => {setChoice("b");onClose();}} className="border-2 border-t-0 bg-mist-800/50 rounded-b-md hover:bg-mist-400/70" src={`/src/assets/bishop_${color}.png`} alt="" />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Promotion;
