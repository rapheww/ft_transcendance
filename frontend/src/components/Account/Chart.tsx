import { Line, LineChart, Tooltip, XAxis, YAxis } from "recharts";

const data = [
  { name: "A", value: 400 },
  { name: "B", value: 300 },
  { name: "C", value: 500 },
  { name: "D", value: 50 },
  { name: "E", value: 145 },
  { name: "F", value: 140 },
  { name: "G", value: 570 },
  { name: "H", value: 410 },
  { name: "I", value: 3000 },
];

export default function Step1() {
  return (
    <div className="w-full h-full flex justify-center items-center">
      <LineChart
        style={{ width: "100%", aspectRatio: 1.618, maxWidth: 600 }}
        responsive
        data={data}
        margin={{
          top: 20,
          right: 20,
          bottom: 5,
          left: 0,
        }}
      >
        <Line
          type="monotone"
          dataKey="value"
          strokeWidth={3}
          stroke="#fff"
          dot={{ stroke: "#22292b", strokeWidth: 2, fill: "#c36fed", r: 6 }}
          name="Elo"
        />
        <XAxis dataKey="name" />
        <YAxis />
        <Tooltip />
      </LineChart>
    </div>
  );
}
