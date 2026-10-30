import confetti from "canvas-confetti";
import { ArrowBigDown, ArrowBigUp, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useAuth, type ProfilType } from "../../AuthProvider";
import { API } from "../utils/api";
import { getStats } from "../utils/utils";
import type { StatsProfil } from "../../Account/Profil/Chart";

interface Props {
  onClose: () => void;
  open: boolean;
  result: string;
  color: string;
  opponentName: string;
  opponentType?: string;
}

function getElo(playerElo: StatsProfil) {
  if (!playerElo) return { elo: 0, diff: 0 };
  const hist = playerElo.elo_history;
  const newElo = playerElo.elo;
  if (hist.length === 1) {
    const diff = -(1000 - newElo);
    return { elo: newElo, diff: diff };
  } else if (hist.length > 1) {
    const eloBefore = hist[hist.length - 2].elo;
    const diff = -(eloBefore - newElo);
    return { elo: newElo, diff: diff };
  } else {
    return { elo: newElo, diff: 0 };
  }
}

const GameOver = ({ open, onClose, result, color, opponentName, opponentType }: Props) => {
  const [profilOps, setProfil] = useState<ProfilType | null>();
  const colorResult: string = result === "0-1" ? "Black Wins" : result === "1-0" ? "White Wins" : "Draw";
  const { profil } = useAuth();
  const playerElo = getStats(profil.username, open);
  const elo: { elo: number; diff: number } = getElo(playerElo);
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
        const response = await fetch(`${API}/users/${opponentName}`);
        if (!response.ok) return;
        const infos = await response.json();
        setProfil(infos);
      } catch (err) {
        console.error(err);
      }
    })();
  }, [open, opponentName]);

  return (
    <div
      className={`
            absolute inset-0 z-40 p-2
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
            <div className="bg-black/90 backdrop-blur-xs border border-white/50 shadow-xl md:shadow-2xl shadow-black max-h-[90vh] overflow-y-auto flex justify-center items-center flex-col rounded-lg p-3 sm:p-5 gap-2">
              <button
                onClick={onClose}
                className="cursor-pointer place-self-end"
              >
                <X size={30} />
              </button>
              <h1 className="text-xl sm:text-2xl font-extrabold">{colorResult}</h1>
              <div className="w-full flex flex-row justify-center py-2 items-center text-center">
                <div className="w-1/3 flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-3 overflow-hidden">
                  <img
                    src={
                      color === "white"
                        ? profil.avatar
                        : (profilOps?.avatar ??
                          "https://media.tenor.com/GQAsycjoZG8AAAAj/scuba-scuba-cat.gif")
                    }
                    alt=""
                    className="size-10 sm:size-14 md:size-20 shrink-0 object-cover rounded-full"
                  />
                  <p className="text-sm sm:text-lg max-w-full truncate">
                    {color === "white" ? profil.username : opponentName}
                  </p>
                </div>
                <p className="w-1/3">{result}</p>
                <div className="w-1/3 flex flex-col sm:flex-row items-center justify-center gap-1 sm:gap-3 overflow-hidden">
                  <img
                    src={
                      color === "black"
                        ? profil.avatar
                        : (profilOps?.avatar ??
                          "https://media.tenor.com/GQAsycjoZG8AAAAj/scuba-scuba-cat.gif")
                    }
                    alt=""
                    className="size-10 sm:size-14 md:size-20 shrink-0 object-cover rounded-full"
                  />
                  <p className="text-sm sm:text-lg max-w-full truncate">
                    {color === "black" ? profil.username : opponentName}
                  </p>
                </div>
              </div>
              {opponentType !== "ai" && (
                <p className="text-sm sm:text-lg flex flex-row items-center gap-1 mt-2">
                {`Elo: ${elo.elo} (${elo.diff > 0 ? `+${elo.diff}` : elo.diff})`}
                {elo.diff > 0 ? (
                  <ArrowBigUp size={20} color={"#227501"} />
                ) : (
                  <ArrowBigDown size={20} color={"#8f0110"} />
                )}
              </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GameOver;
