// src/components/RiskDistributionChart.tsx  (DROP-IN REPLACEMENT)

import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { DayBucket } from "@/api/types";

export function RiskDistributionChart({ data }: { data: DayBucket[] }) {
  // Fills the height of its parent; no internal title/card here.
  return (
    <div className="w-full h-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data}>
          <CartesianGrid vertical={false} />
          <XAxis dataKey="bucket" />
          <YAxis allowDecimals={false} />
          <Tooltip />
          <Bar dataKey="count" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}