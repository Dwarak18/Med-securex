
'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { Area, AreaChart, CartesianGrid, XAxis, YAxis } from 'recharts';

const chartData = [
  { month: 'January', apiShield: 186, medBox: 80 },
  { month: 'February', apiShield: 305, medBox: 200 },
  { month: 'March', apiShield: 237, medBox: 120 },
  { month: 'April', apiShield: 73, medBox: 190 },
  { month: 'May', apiShield: 209, medBox: 130 },
  { month: 'June', apiShield: 214, medBox: 140 },
];

const chartConfig = {
  apiShield: {
    label: 'API Shield',
    color: 'hsl(var(--chart-1))',
  },
  medBox: {
    label: 'MED Box',
    color: 'hsl(var(--chart-2))',
  },
};

export function AlertsOverTimeChart() {
  return (
    <Card className="rounded-2xl shadow-lg">
      <CardHeader>
        <CardTitle>Alerts Over Time</CardTitle>
        <CardDescription>Total alerts by source over the last 6 months</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[300px] w-full">
          <AreaChart data={chartData} margin={{ left: -20, right: 10, top: 10, bottom: 0 }}>
            <CartesianGrid vertical={false} strokeDasharray="3 3" />
            <XAxis dataKey="month" tickLine={false} axisLine={false} tickMargin={8} />
            <YAxis tickLine={false} axisLine={false} tickMargin={8} />
            <ChartTooltip content={<ChartTooltipContent 
                formatter={(value, name) => (
                    <div className="flex items-center">
                        <span className="w-2.5 h-2.5 rounded-full mr-2" style={{backgroundColor: chartConfig[name as keyof typeof chartConfig].color}}></span>
                        <span>{chartConfig[name as keyof typeof chartConfig].label}: {value}</span>
                    </div>
                )}
            />} />
            <defs>
              <linearGradient id="fillApiShield" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-apiShield)" stopOpacity={0.8} />
                <stop offset="95%" stopColor="var(--color-apiShield)" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="fillMedBox" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-medBox)" stopOpacity={0.8} />
                <stop offset="95%" stopColor="var(--color-medBox)" stopOpacity={0.1} />
              </linearGradient>
              <filter id="glow" x="-50%" y="-50%" width="200%" height="200%">
                  <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor="hsl(var(--chart-1))" />
              </filter>
              <filter id="glow2" x="-50%" y="-50%" width="200%" height="200%">
                  <feDropShadow dx="0" dy="0" stdDeviation="4" floodColor="hsl(var(--chart-2))" />
              </filter>
            </defs>
            <Area
              dataKey="medBox"
              type="natural"
              fill="url(#fillMedBox)"
              stroke="var(--color-medBox)"
              stackId="a"
              strokeWidth={2}
              filter="url(#glow2)"
            />
            <Area
              dataKey="apiShield"
              type="natural"
              fill="url(#fillApiShield)"
              stroke="var(--color-apiShield)"
              stackId="a"
              strokeWidth={2}
              filter="url(#glow)"
            />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
