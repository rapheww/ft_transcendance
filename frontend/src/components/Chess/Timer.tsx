import { useEffect, useState } from "react";

interface Props {
  time: number | null;
  turn: boolean;
  lastMoveAt?: string | null;
  setGameOver: React.Dispatch<React.SetStateAction<boolean>>;
}

const Timer = ({ time, turn, lastMoveAt, setGameOver }: Props) => {
  const [clockNow, setClockNow] = useState(() => Date.now());
  const [startedAt] = useState(() => Date.now());

  const lastMoveTimestamp = lastMoveAt ? Date.parse(lastMoveAt) : Number.NaN;
  const clockStart = Number.isFinite(lastMoveTimestamp)
    ? lastMoveTimestamp
    : startedAt;
  const elapsed =
    turn && time !== null
      ? Math.max(0, Math.floor((clockNow - clockStart) / 1000))
      : 0;
  const timeLeft = time === null ? null : Math.max(0, time - elapsed);

  useEffect(() => {
    if (time === null || !turn) return;
    const id = window.setInterval(() => {
      const now = Date.now();
      setClockNow(now);
      if (Math.floor((now - clockStart) / 1000) >= time) {
        setGameOver(true);
      }
    }, 250);
    return () => window.clearInterval(id);
  }, [clockStart, setGameOver, time, turn]);

  if (timeLeft === null) {
    return <h2 className="font-bold text-2xl">--:--</h2>;
  }

  const minuts = Math.floor(timeLeft / 60);
  const seconds = timeLeft % 60;
  return (
    <h2 className="font-bold text-2xl">
      {`${minuts}: ${seconds < 10 ? `0${seconds}` : seconds}`}
    </h2>
  );
};

export default Timer;
