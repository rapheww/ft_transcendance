import { useEffect, useState } from "react";


interface Props{
    time: number;
    turn: boolean;
}

const Timer = ({time, turn}: Props) => {
    const [timeLeft, setTimeLeft] = useState<number>(time);

    useEffect(() => {
        if(timeLeft <= 0 || !turn) return;
        const id = setTimeout( () => setTimeLeft((t) => t - 1), 1000);
        return () => clearTimeout(id);
    }, [timeLeft, turn]);

    const minuts = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    return (
        <h2 className="font-bold text-2xl">
            {`${minuts}: ${seconds < 10 ? `0${seconds}`:seconds}`}
        </h2>
    );
};

export default Timer;
