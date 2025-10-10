
'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, Legend, Tooltip } from 'recharts';

const chartData = [
  { month: 'May', ssn: 120, dob: 150, address: 80 },
  { month: 'June', ssn: 180, dob: 210, address: 110 },
  { month: 'July', ssn: 220, dob: 250, address: 140 },
  { month: 'August', ssn: 250, dob: 280, address: 160 },
  { month: 'September', ssn: 230, dob: 260, address: 150 },
  { month: 'October', ssn: 280, dob: 310, address: 180 },
];

const chartConfig = {
  ssn: { label: 'SSN', color: 'hsl(var(--chart-1))' },
  dob: { label: 'Date of Birth', color: 'hsl(var(--chart-2))' },
  address: { label: 'Address', color: 'hsl(var(--chart-3))' },
};

export function PiiOverTimeChart() {
  const [activeBar, setActiveBar] = useState<string | null>(null);

  const getGlowFilter = (barKey: string) => {
    if (activeBar === barKey) {
      const color = chartConfig[barKey as keyof typeof chartConfig].color;
      return `drop-shadow(0 0 8px ${color})`;
    }
    return 'drop-shadow(0 1px 2px rgb(0 0 0 / 0.1))';
  };


  return (
    <Card className="rounded-2xl shadow-lg">
      <CardHeader>
        <CardTitle>Scrubbed PII Over Time</CardTitle>
        <CardDescription>Monthly count of scrubbed PII fields by type.</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[350px] w-full">
          <BarChart 
            data={chartData} 
            margin={{ top: 10, right: 20, left: -10, bottom: 5 }}
            barGap={4}
            barCategoryGap="20%"
            onMouseMove={(state) => {
                if (state.activePayload && state.activePayload.length) {
                    setActiveBar(state.activePayload[0].dataKey);
                } else {
                    setActiveBar(null);
                }
            }}
            onMouseLeave={() => setActiveBar(null)}
          >
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="month" tickLine={false} axisLine={false} tickMargin={8} />
            <YAxis tickLine={false} axisLine={false} tickMargin={8} stroke="hsl(var(--muted-foreground))" />
            <Tooltip
                content={<ChartTooltipContent />}
                cursor={{ fill: 'hsl(var(--accent) / 0.5)' }}
            />
            <Legend />
            <Bar 
                dataKey="ssn" 
                stackId="a" 
                fill="var(--color-ssn)" 
                stroke="hsl(var(--background))"
                strokeWidth={2}
                style={{ filter: getGlowFilter('ssn'), transition: 'filter 0.2s ease-in-out' }}
            />
            <Bar 
                dataKey="dob" 
                stackId="a" 
                fill="var(--color-dob)" 
                stroke="hsl(var(--background))"
                strokeWidth={2}
                style={{ filter: getGlowFilter('dob'), transition: 'filter 0.2s ease-in-out' }}
            />
            <Bar 
                dataKey="address" 
                stackId="a" 
                fill="var(--color-address)"
                stroke="hsl(var(--background))"
                strokeWidth={2}
                style={{ filter: getGlowFilter('address'), transition: 'filter 0.2s ease-in-out' }}
            />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
