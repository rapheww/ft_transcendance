import confetti from "canvas-confetti";
import { X } from "lucide-react";
import { useEffect } from "react";

interface Props {
  onClose: () => void;
  open: boolean;
  result: string;
  color: string;
}

const GameOver = ({ open, onClose, result, color }: Props) => {
  useEffect(() => {
    if (!open) return;
    if(result === "0-1" && color != "black" || result === "1-0" && color != "white") return;
    let count = 200;
    let defaults = {
      origin: { y: 0.7 },
    };

    function fire(particleRatio: number, opts: confetti.Options | undefined) {
      confetti({
        ...defaults,
        ...opts,
        particleCount: Math.floor(count * particleRatio),
      });
    }

    fire(0.25, {
      spread: 26,
      startVelocity: 55,
    });
    fire(0.2, {
      spread: 60,
    });
    fire(0.35, {
      spread: 100,
      decay: 0.91,
      scalar: 0.8,
    });
    fire(0.1, {
      spread: 120,
      startVelocity: 25,
      decay: 0.92,
      scalar: 1.2,
    });
    fire(0.1, {
      spread: 120,
      startVelocity: 45,
    });
  }, [open]);

  const colorResult: string = result === "0-1" ? "Black Wins" : "White Wins"
  return (
    <div
      className={`
            absolute inset-0 z-40
            flex justify-center items-center
            transition-opacity duration-500 ease-out
            ${open ? "opacity-100" : "opacity-0 pointer-events-none"}
            `}
    >
      <div
        className={`
                    w-[90%] max-w-2xl
                    transition-all duration-500 ease-out
                    ${open ? "opacity-100 scale-100" : "opacity-0 scale-95"}
                    `}
      >
        <div className="w-full flex justify-center items-center">
          <div className="flex flex-col text-white w-full">
            <div className="bg-mist-800 max-h-[90vh] flex justify-center items-center flex-col rounded-lg p-5 gap-2">
              <button
                onClick={onClose}
                className="cursor-pointer place-self-end"
              >
                <X size={30} />
              </button>
              <h1 className="text-2xl font-extrabold">{colorResult}</h1>
              <p className="text-2xl">{result}</p>
              <p className="mt-2 text-sm">click on the king at the top left to go to home page</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameOver;
