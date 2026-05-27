import ReactECharts from "echarts-for-react";

interface GameHistoryChartProps {
  placements: number[];
}

export default function GameHistoryChart({ placements }: GameHistoryChartProps) {
  const option = {
    tooltip: {
      trigger: "axis",
      backgroundColor: "#0f1524",
      borderColor: "#1c2640",
      textStyle: { color: "#fff", fontSize: 12 },
      formatter: (params: { dataIndex: number; value: number }[]) => {
        const p = params[0];
        return `Game ${p.dataIndex + 1}<br/>Placement: <b>#${p.value}</b>`;
      },
    },
    grid: { top: 20, right: 20, bottom: 30, left: 40 },
    xAxis: {
      type: "category",
      data: placements.map((_, i) => String(i + 1)),
      axisLabel: { color: "#9ca3af", fontSize: 10 },
      axisLine: { lineStyle: { color: "#1c2640" } },
    },
    yAxis: {
      type: "value",
      min: 1,
      max: 8,
      inverse: true,
      axisLabel: { color: "#9ca3af", fontSize: 10 },
      axisLine: { lineStyle: { color: "#1c2640" } },
      splitLine: { lineStyle: { color: "#1c264040" } },
    },
    series: [
      {
        type: "line",
        data: placements,
        smooth: true,
        symbol: "circle",
        symbolSize: 6,
        lineStyle: { color: "#0ac8b9", width: 2 },
        itemStyle: {
          color: (params: { value: number }) =>
            params.value <= 4 ? "#0ac8b9" : "#c8aa6e",
        },
        areaStyle: {
          color: {
            type: "linear",
            x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: "rgba(10, 200, 185, 0.3)" },
              { offset: 1, color: "rgba(10, 200, 185, 0)" },
            ],
          },
        },
      },
    ],
  };

  return (
    <div className="bg-dark-700 border border-dark-600 rounded-xl p-4">
      <h3 className="text-sm font-semibold text-gold mb-3">Game History</h3>
      <ReactECharts
        option={option}
        style={{ height: 240 }}
        opts={{ renderer: "svg" }}
      />
    </div>
  );
}
