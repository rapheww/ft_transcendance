import { useEffect, useRef, useState } from "react";

interface Props {
  time: number;
  turn: boolean;
  bonus: number;
  toAdd: boolean;
  setGameOver: React.Dispatch<React.SetStateAction<boolean>>;
}

const Timer = ({ time, turn, bonus, toAdd, setGameOver }: Props) => {
  const [timeLeft, setTimeLeft] = useState<number>(time);
  const tickStart = useRef(0); // moment où le tick en cours a démarré
  const carried = useRef(0); // millisecondes déjà écoulées dans la seconde en cours

  useEffect(() => {
    if (!turn) return;
    if (timeLeft <= 0) {
      setGameOver(true);
      return;
    }
    let fired = false;
    tickStart.current = Date.now()
    const id = setTimeout(() => {
      fired = true;
      carried.current = 0;
      setTimeLeft((t) => t - 1);
    }, 1000 - carried.current);
    return () => {
      clearTimeout(id);
       if(!fired) carried.current += Date.now() - tickStart.current;
    }
  }, [timeLeft, turn]);

  useEffect(() => {
    if (toAdd) {
      setTimeLeft((t) => t + bonus);
    }
  }, [toAdd]);

  const minuts = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  return (
    <h2 className="font-bold text-2xl">
      {`${minuts}: ${seconds < 10 ? `0${seconds}` : seconds}`}
    </h2>
  );
};

export default Timer;
