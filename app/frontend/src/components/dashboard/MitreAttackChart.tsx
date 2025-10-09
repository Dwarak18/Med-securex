
'use client';

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { ChartContainer, ChartTooltip } from '@/components/ui/chart';
import { PieChart, Pie, Cell } from 'recharts';
import { motion } from 'framer-motion';
import ttpsData from '@/components/dashboard/mitre_attack_dataset.json';

const initialChartConfig = {
  alerts: {
    label: 'Alerts',
  },
};

// Define a consistent color palette for the chart
const COLORS = [
  'hsl(var(--chart-1))',
  'hsl(var(--chart-2))',
  'hsl(var(--chart-3))',
  'hsl(var(--chart-4))',
  'hsl(var(--chart-5))',
];

export function MitreAttackChart({ className }: { className?: string }) {
  const [chartData, setChartData] = React.useState<{ name: string; value: number; fill: string; }[]>([]);
  const [chartConfig, setChartConfig] = React.useState(initialChartConfig);
  const [totalIncidents, setTotalIncidents] = React.useState(0);
  const [activeIndex, setActiveIndex] = React.useState<number | null>(null);

  React.useEffect(() => {
    // Process the TTPs data to get counts for each attack type
    const tacticCounts: { [key: string]: number } = {};
    ttpsData.forEach((item: any) => {
      const tactic = item.AttackType;
      if (tactic) {
        tacticCounts[tactic] = (tacticCounts[tactic] || 0) + 1;
      }
    });
    
    const total = Object.values(tacticCounts).reduce((sum, count) => sum + count, 0);
    setTotalIncidents(total);

    const sortedTactics = Object.entries(tacticCounts)
      .sort(([, a], [, b]) => b - a);

    const top4 = sortedTactics.slice(0, 4);
    const otherCount = sortedTactics.slice(4).reduce((sum, [, count]) => sum + count, 0);

    const processedData = top4.map(([name, value], index) => ({
      name,
      value,
      fill: COLORS[index % COLORS.length],
    }));

    if (otherCount > 0) {
      processedData.push({
        name: 'Others',
        value: otherCount,
        fill: COLORS[4 % COLORS.length],
      });
    }

    const newConfig = processedData.reduce((acc, item) => {
        acc[item.name] = { label: item.name, color: item.fill };
        return acc;
    }, { ...initialChartConfig });

    setChartData(processedData);
    // @ts-ignore
    setChartConfig(newConfig);

  }, []);

  const onPieEnter = (_: any, index: number) => {
    setActiveIndex(index);
  };

  const onPieLeave = () => {
    setActiveIndex(null);
  };


  return (
    <Card className={`rounded-2xl shadow-lg h-full flex flex-col overflow-hidden ${className}`}>
      <div className="relative flex flex-col h-full">
        <CardHeader className="items-center pb-2">
          <CardTitle>MITRE ATT&amp;CK Techniques</CardTitle>
          <CardDescription>Top 4 observed techniques</CardDescription>
        </CardHeader>
        <CardContent className="flex-1 flex flex-col items-center justify-center p-4 pt-6">
          <div
            className="relative w-full h-[250px] flex items-center justify-center"
          >
            <ChartContainer
              config={chartConfig}
              className="mx-auto aspect-square h-full"
            >
              <PieChart>
                <ChartTooltip
                  cursor={false}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload;
                      const percentage = ((data.value / totalIncidents) * 100).toFixed(1);
                      return (
                        <div className="rounded-lg border bg-background/80 backdrop-blur-sm p-2 shadow-sm text-xs">
                          <p className="font-bold">{data.name}</p>
                          <p>Count: {data.value.toLocaleString()}</p>
                          <p>Percentage: {percentage}%</p>
                        </div>
                      );
                    }
                    return null;
                  }}
                />
                <Pie
                  data={chartData}
                  dataKey="value"
                  nameKey="name"
                  innerRadius="60%"
                  strokeWidth={2}
                  stroke="hsl(var(--card))"
                  cornerRadius={10}
                  onMouseEnter={onPieEnter}
                  onMouseLeave={onPieLeave}
                >
                  {chartData.map((entry, index) => (
                    <Cell 
                        key={`cell-${entry.name}`} 
                        fill={entry.fill}
                        style={{
                            transform: activeIndex === index ? 'scale(1.05)' : 'scale(1)',
                            transformOrigin: 'center center',
                            transition: 'transform 0.2s ease-in-out',
                        }}
                    />
                  ))}
                </Pie>
              </PieChart>
            </ChartContainer>
            <motion.div
              className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none"
              initial={{ opacity: 1 }}
              animate={{ opacity: activeIndex !== null ? 0 : 1 }}
              transition={{ duration: 0.2 }}
            >
              <span className="text-3xl font-bold">{totalIncidents.toLocaleString()}</span>
              <span className="text-xs text-muted-foreground">Total Incidents</span>
            </motion.div>
          </div>
          <div className="w-full mt-4 flex flex-wrap justify-center gap-x-4 gap-y-2 text-xs">
            {chartData.map((entry) => (
              <div key={entry.name} className="flex items-center gap-2">
                <div
                  className="h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: entry.fill }}
                />
                <span>{entry.name}</span>
              </div>
            ))}
          </div>
        </CardContent>
      </div>
    </Card>
  );
}
