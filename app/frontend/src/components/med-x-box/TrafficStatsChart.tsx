'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { LineChart, Line, CartesianGrid, XAxis, YAxis, Legend } from 'recharts';

const chartData = [
  { time: '10:00', packets: 2200, flows: 120 },
  { time: '10:05', packets: 2500, flows: 150 },
  { time: '10:10', packets: 2800, flows: 180 },
  { time: '10:15', packets: 2300, flows: 130 },
  { time: '10:20', packets: 3100, flows: 200 },
  { time: '10:25', packets: 2600, flows: 160 },
  { time: '10:30', packets: 2900, flows: 190 },
];

const chartConfig = {
  packets: {
    label: 'Packets/sec',
    color: 'hsl(var(--chart-1))',
  },
  flows: {
    label: 'Flows',
    color: 'hsl(var(--chart-2))',
  },
};

export function TrafficStatsChart() {
  return (
    <Card className="rounded-2xl shadow-lg h-full">
      <CardHeader>
        <CardTitle>Network Traffic Stats</CardTitle>
        <CardDescription>Real-time packets per second and network flows.</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[300px] w-full">
          <LineChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="time" tickLine={false} axisLine={false} tickMargin={8} />
            <YAxis yAxisId="left" orientation="left" stroke="var(--color-packets)" tickLine={false} axisLine={false} tickMargin={8} />
            <YAxis yAxisId="right" orientation="right" stroke="var(--color-flows)" tickLine={false} axisLine={false} tickMargin={8} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Legend />
            <Line yAxisId="left" type="monotone" dataKey="packets" stroke="var(--color-packets)" strokeWidth={2} dot={false} />
            <Line yAxisId="right" type="monotone" dataKey="flows" stroke="var(--color-flows)" strokeWidth={2} dot={false} />
          </LineChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
