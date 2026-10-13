interface PromotionProps {
  open: boolean;
  onClose: () => void;
  setChoice: (piece: "q" | "r" | "b" | "n") => void;
}

const Promotion = ({ open, onClose, setChoice }: PromotionProps) => {
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
                    w-[90%] max-w-6xl
                    transition-all duration-500 ease-out
                    ${open ? "opacity-100 scale-100" : "opacity-0 scale-95"}
                    `}
      >
        <div
          onClick={() => {
            setChoice("r");
            onClose();
          }}
          className="w-full h-full flex flex-col justify-center items-center bg-mist-800 gap-2 p-3"
        >
          <button onClick={() => {setChoice("q");onClose();}} className="btn btn-primary w-[50%]">q</button>
          <button onClick={() => {setChoice("n");onClose();}} className="btn btn-primary w-[50%]">n</button>
          <button onClick={() => {setChoice("r");onClose();}} className="btn btn-primary w-[50%]">r</button>
          <button onClick={() => {setChoice("b");onClose();}} className="btn btn-primary w-[50%]">b</button>
        </div>
      </div>
    </div>
  );
};

export default Promotion;
