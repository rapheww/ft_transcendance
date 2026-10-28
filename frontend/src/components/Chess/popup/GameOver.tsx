import confetti from "canvas-confetti";
import { X } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth, type ProfilType } from "../../AuthProvider";
import { API } from "../utils/api";

interface Props {
  onClose: () => void;
  open: boolean;
  result: string;
  color: string;
  opponentName: string;
}

const GameOver = ({ open, onClose, result, color, opponentName }: Props) => {
  const [profilOps, setProfil] = useState<ProfilType | null>();
  useEffect(() => {
    if (!open) return;
    if (
      (result === "0-1" && color != "black") ||
      (result === "1-0" && color != "white")
    )
      return;
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

  useEffect(() => {
    if (!open || !opponentName) return;
    (async () => {
      try {
        const response = await fetch(
          `${API}/users/${opponentName}`,
        );
        if (!response.ok) return;
        const infos = await response.json();
        setProfil(infos);
      } catch (err) {
        console.error(err);
      }
    })();
  }, [open, opponentName]);

  const colorResult: string = result === "0-1" ? "Black Wins" : "White Wins";
  const { profil } = useAuth();
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
            <div className="bg-black/90 backdrop-blur-xs border border-white/50 shadow-xl md:shadow-2xl shadow-black max-h-[90vh] flex justify-center items-center flex-col rounded-lg p-5 gap-2">
              <button
                onClick={onClose}
                className="cursor-pointer place-self-end"
              >
                <X size={30} />
              </button>
              <h1 className="text-2xl font-extrabold">{colorResult}</h1>
              <div className="border w-full flex flex-row justify-center h-20 lg:h-30 items-center text-center">
                <div className="w-1/3 h-full flex items-center justify-center gap-3 lg:gap-5">
                  <img
                    src={color === "white" ? profil.avatar : profilOps?.avatar ?? 'https://media.tenor.com/GQAsycjoZG8AAAAj/scuba-scuba-cat.gif'}
                    alt=""
                    className=" h-[80%] object-cover rounded-full"
                  />
                  <p className="text-lg lg:text-xl">
                    {color === "white" ? profil.username : opponentName}
                  </p>
                </div>
                <p className="w-1/3">{result}</p>
                <div className="w-1/3 h-full flex items-center justify-center gap-3 lg:gap-5">
                  <img
                    src={color === "black" ? profil.avatar : profilOps?.avatar ?? 'https://media.tenor.com/GQAsycjoZG8AAAAj/scuba-scuba-cat.gif'}
                    alt=""
                    className=" h-[80%] object-cover rounded-full"
                  />
                  <p className="text-lg lg:text-xl">
                    {color === "black" ? profil.username : opponentName}
                  </p>
                </div>
              </div>
              <p className="mt-2 text-sm">elo +1000</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameOver;
