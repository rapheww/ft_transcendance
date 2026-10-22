import { useEffect, useState } from "react";
import { Line, LineChart, Tooltip, XAxis, YAxis } from "recharts";
import { useAuth } from "../../AuthProvider";

type StatsProfil = {
  elo: number;
  games_played: number;
  wins: number;
  losses: number;
  draws: number;
  win_rate: number;
  username: string;
  elo_history: [
    {
      date: string;
      elo: number;
    },
  ];
};

const emptyStats: StatsProfil = {
  elo: 0,
  games_played: 0,
  wins: 0,
  losses: 0,
  draws: 0,
  win_rate: 0,
  username: "unknown",
  elo_history: [
    {
      date: "today",
      elo: 0,
    },
  ],
};

interface ChartProps {
  username: string;
}

export default function Chart({ username }: ChartProps) {
  const [stats, setStats] = useState<StatsProfil>(emptyStats);
  const { token } = useAuth();

  useEffect(() => {
    if (!username || username === 'unknown') return;
    (async () => {
      try {
        const response = await fetch(
          `http://127.0.0.1:8000/api/stats/player/${username}`,
          {
            headers: { Authorization: `Bearer ${token}` },
          },
        );
        if (!response.ok) return;
        const infos = await response.json();
        setStats(infos);
      } catch (err) {
        console.error(err);
      }
    })();
  }, [username]);

  const chartData = stats.elo_history.map((s) => {
    const date = new Date(s.date)
    return {
      ...s,
      date: date.toLocaleString("fr-FR", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit"
    })
    };
  });

  //garde 1 jours sur 2 a partir de 15 jours et et 1 jours sur 15 a partir de 3 mois
  const displayData =
  chartData.length > 90
    ? chartData.filter((_, i) => i % 15 === 0 || i === chartData.length - 1)
    : chartData.length > 20
      ? chartData.filter((_, i) => i % 2 === 0 || i === chartData.length - 1)
      : chartData;

  if (chartData.length > 1) {
    return (
      <div className="w-full h-full flex justify-center items-center">
        <LineChart
          style={{ width: "100%", aspectRatio: 1.618, maxWidth: 600 }}
          responsive
          data={displayData}
          margin={{
            top: 20,
            right: 20,
            bottom: 5,
            left: 0,
          }}
        >
          <Line
            type="monotone"
            dataKey="elo"
            strokeWidth={3}
            stroke="#fff"
            name="Elo"
          />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip
            contentStyle={{
              backgroundColor: "#fff",
              border: "1px solid #ccc",
              color: "#000",
            }}
            labelStyle={{
              color: "#000",
            }}
            itemStyle={{
              color: "#000",
            }}
          />
        </LineChart>
      </div>
    );
  } else {
    return (
      <div className="w-full h-full flex justify-center items-center">
        <p>{`Current elo : ${stats.elo} --> play games to get more stats`}</p>
      </div>
    );
  }
}