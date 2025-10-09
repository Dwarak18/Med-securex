'use client';

import * as React from 'react';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '@/components/ui/card';
import { ChartContainer } from '@/components/ui/chart';
import {
  RadialBarChart,
  RadialBar,
  PolarAngleAxis,
  Legend,
  Tooltip,
  Cell,
} from 'recharts';

const chartData = [
  { name: 'Windows', value: 450, fill: 'url(#gradWindows)' },
  { name: 'Linux', value: 300, fill: 'url(#gradLinux)' },
  { name: 'macOS', value: 150, fill: 'url(#gradMacOS)' },
  { name: 'Other', value: 100, fill: 'url(#gradOther)' },
];

const chartConfig = {
  value: { label: 'Alerts' },
  Windows: { label: 'Windows', color: 'hsl(var(--chart-1))' },
  Linux: { label: 'Linux', color: 'hsl(var(--chart-2))' },
  macOS: { label: 'macOS', color: 'hsl(var(--chart-3))' },
  Other: { label: 'Other', color: 'hsl(var(--destructive))' },
};

export function TopSystemsChart() {
  const totalAlerts = React.useMemo(() => {
    return chartData.reduce((acc, curr) => acc + curr.value, 0);
  }, []);

  return (
    <Card className="rounded-2xl shadow-lg h-full flex flex-col">
      <CardHeader className="items-center pb-2">
        <CardTitle>Alerts by System OS</CardTitle>
        <CardDescription>Top operating systems generating alerts</CardDescription>
      </CardHeader>
      <CardContent className="flex-1 pb-0 flex items-center justify-center">
        <ChartContainer
          config={chartConfig}
          className="mx-auto aspect-square max-h-[250px] w-full"
        >
          <RadialBarChart
            data={chartData}
            innerRadius="30%"
            outerRadius="100%"
            startAngle={90}
            endAngle={-270}
          >
            <defs>
              <linearGradient id="gradWindows" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--chart-1))" stopOpacity={0.8} />
                <stop offset="95%" stopColor="hsl(var(--chart-1))" stopOpacity={0.2} />
              </linearGradient>
              <linearGradient id="gradLinux" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--chart-2))" stopOpacity={0.8} />
                <stop offset="95%" stopColor="hsl(var(--chart-2))" stopOpacity={0.2} />
              </linearGradient>
              <linearGradient id="gradMacOS" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--chart-3))" stopOpacity={0.8} />
                <stop offset="95%" stopColor="hsl(var(--chart-3))" stopOpacity={0.2} />
              </linearGradient>
              <linearGradient id="gradOther" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="hsl(var(--destructive))" stopOpacity={0.8} />
                <stop offset="95%" stopColor="hsl(var(--destructive))" stopOpacity={0.2} />
              </linearGradient>
            </defs>

            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const data = payload[0].payload;
                  const percentage = ((data.value / totalAlerts) * 100).toFixed(1);
                  return (
                    <div className="rounded-lg border bg-background p-2 shadow-sm">
                      <div className="grid grid-cols-2 gap-2">
                        <div className="flex flex-col">
                          <span className="text-[0.70rem] uppercase text-muted-foreground">
                            {data.name}
                          </span>
                          <span className="font-bold text-muted-foreground">
                            {data.value.toLocaleString()}
                          </span>
                        </div>
                        <div className="flex flex-col">
                          <span className="text-[0.70rem] uppercase text-muted-foreground">
                            Percent
                          </span>
                          <span className="font-bold">{percentage}%</span>
                        </div>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />

            <PolarAngleAxis type="number" domain={[0, totalAlerts]} tick={false} />

            <RadialBar
              dataKey="value"
              background
              cornerRadius={10}
              animationBegin={0}
              animationDuration={800}
              isAnimationActive={true}
            >
              {chartData.map((entry) => (
                <Cell key={`cell-${entry.name}`} fill={entry.fill} />
              ))}
            </RadialBar>

            <Legend
            
              iconSize={20}
              layout="vertical"
              align="right"
              verticalAlign="middle"
              formatter={(value) => chartConfig[value]?.label}
            />
          </RadialBarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
