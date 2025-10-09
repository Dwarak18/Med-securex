
'use client';

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent, ChartLegend, ChartLegendContent } from '@/components/ui/chart';
import { PieChart, Pie, Cell } from 'recharts';

const chartData = [
  { source: 'API Shield', alerts: 65, fill: '#00BFFF' },
  { source: 'MED Box', alerts: 35, fill: '#00FFB2' },
];

const chartConfig = {
  alerts: {
    label: 'Alerts',
  },
  'API Shield': {
    label: 'API Shield',
    color: '#00BFFF',
  },
  'MED Box': {
    label: 'MED Box',
    color: '#00FFB2',
  },
};

export function AlertSourcesChart({ className }: { className?: string }) {
  const [activeIndex, setActiveIndex] = React.useState<number | null>(null);

  const totalAlerts = React.useMemo(() => {
    return chartData.reduce((acc, curr) => acc + curr.alerts, 0);
  }, []);

  const onPieEnter = (_: any, index: number) => {
    setActiveIndex(index);
  };

  const onPieLeave = () => {
    setActiveIndex(null);
  };

  return (
    <Card className={`rounded-2xl shadow-lg h-full flex flex-col ${className}`}>
      <CardHeader className="items-center pb-2">
        <CardTitle>Alert Sources</CardTitle>
        <CardDescription>Last 24 hours</CardDescription>
      </CardHeader>
      <CardContent className="flex-1 flex flex-col items-center justify-center p-4">
        <div className="relative w-full h-[250px] flex items-center justify-center">
            <ChartContainer config={chartConfig} className="mx-auto aspect-square h-full">
            <PieChart>
                <ChartTooltip
                cursor={false}
                content={<ChartTooltipContent hideLabel />}
                />
                <Pie
                data={chartData}
                dataKey="alerts"
                nameKey="source"
                innerRadius="60%"
                strokeWidth={0}
                onMouseEnter={onPieEnter}
                onMouseLeave={onPieLeave}
                >
                {chartData.map((entry, index) => (
                    <Cell 
                        key={`cell-${entry.source}`} 
                        fill={entry.fill} 
                        style={{
                            transform: activeIndex === index ? 'scale(1.05)' : 'scale(1)',
                            transformOrigin: 'center center',
                            transition: 'transform 0.2s ease-in-out',
                        }}
                    />
                ))}
                </Pie>
                <ChartLegend
                content={<ChartLegendContent nameKey="source" />}
                verticalAlign="bottom"
                align="center"
                wrapperStyle={{
                    position: 'relative',
                    bottom: '10px',
                    boxSizing: 'content-box',
                }}
                />
            </PieChart>
            </ChartContainer>
        </div>
      </CardContent>
    </Card>
  );
}
