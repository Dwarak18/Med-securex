'use client';

import * as React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { Scatter, ScatterChart, XAxis, YAxis, CartesianGrid, ZAxis, Legend, ResponsiveContainer, Brush } from 'recharts';
import type { TTP } from '@/types';
import { Button } from '@/components/ui/button';
import { useMemo } from 'react';

const tacticColorPalette: Record<string, string> = {
  'Initial Access': 'hsl(var(--bubble-1))',
  'Execution': 'hsl(var(--bubble-2))',
  'Persistence': 'hsl(var(--bubble-3))',
  'Privilege Escalation': 'hsl(var(--bubble-4))',
  'Defense Evasion': 'hsl(var(--bubble-5))',
  'Credential Access': 'hsl(var(--bubble-6))',
  'Discovery': 'hsl(var(--bubble-1))',
  'Lateral Movement': 'hsl(var(--bubble-2))',
  'Collection': 'hsl(var(--bubble-3))',
  'Command and Control': 'hsl(var(--bubble-4))',
  'Exfiltration': 'hsl(var(--bubble-5))',
  'Impact': 'hsl(var(--bubble-6))',
  'Malware': 'hsl(var(--bubble-1))',
  'Exploit': 'hsl(var(--bubble-2))',
  'Phishing': 'hsl(var(--bubble-3))',
  'Brute Force': 'hsl(var(--bubble-4))'
};

const tacticYAxisMap: Record<string, number> = {
  'Initial Access': 80,
  'Execution': 75,
  'Persistence': 70,
  'Privilege Escalation': 65,
  'Defense Evasion': 60,
  'Credential Access': 55,
  'Discovery': 50,
  'Lateral Movement': 45,
  'Collection': 72,
  'Command and Control': 68,
  'Exfiltration': 62,
  'Impact': 58,
  'Malware': 85,
  'Exploit': 78,
  'Phishing': 52,
  'Brute Force': 48,
};

const getTacticColor = (tactic: string) => {
  return tacticColorPalette[tactic] || 'hsl(var(--bubble-5))';
};

const getTacticYValue = (tactic: string) => {
    return tacticYAxisMap[tactic] || 50;
}

interface BubbleChartProps {
  ttps: TTP[];
  onBubbleClick: (tactic: string | null) => void;
}

export function TTPsBubbleChart({ ttps, onBubbleClick }: BubbleChartProps) {

  const chartData = useMemo(() => {
    return ttps.map(ttp => ({
      x: ttp.count,
      y: getTacticYValue(ttp.tactic) + (Math.random() - 0.5) * 20, // Increased jitter
      z: ttp.count,
      tactic: ttp.tactic,
      name: ttp.name,
      id: ttp.id
    }));
  }, [ttps]);

  const tactics = useMemo(() => {
      const uniqueTactics = [...new Set(chartData.map(d => d.tactic))];
      return uniqueTactics;
  }, [chartData]);


  return (
    <Card className="rounded-2xl shadow-lg">
      <CardHeader>
        <CardTitle className="text-center">TTP Tactics Overview</CardTitle>
        <CardDescription className="text-center">Bubble size represents incident count. Click a bubble to filter.</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={{}} className="h-[450px] w-full">
            <ResponsiveContainer>
                <ScatterChart
                    margin={{
                        top: 20,
                        right: 20,
                        bottom: 40,
                        left: 20,
                    }}
                    >
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                        type="number" 
                        dataKey="x" 
                        name="count" 
                        label={{ value: "Incident Count", position: "insideBottom", offset: -10 }}
                        scale="log"
                        domain={['dataMin', 'dataMax']}
                        tickFormatter={(value) => value.toLocaleString()}
                    />
                    <YAxis 
                        type="number" 
                        dataKey="y" 
                        name="technique" 
                        label={{ value: "Technique Spread", angle: -90, position: "insideLeft" }}
                        domain={[30, 100]}
                        tick={false}
                    />
                    <ZAxis type="number" dataKey="z" range={[100, 2000]} name="count" />
                    <ChartTooltip 
                        cursor={{ strokeDasharray: '3 3' }} 
                        content={({ active, payload }) => {
                            if (active && payload && payload.length) {
                                const data = payload[0].payload;
                                return (
                                    <div className="rounded-lg border bg-background/80 backdrop-blur-sm p-2 shadow-sm text-xs">
                                        <p className="font-bold">{data.name} ({data.id})</p>
                                        <p>Tactic: {data.tactic}</p>
                                        <p>Count: {data.z}</p>
                                    </div>
                                );
                            }
                            return null;
                        }}
                    />
                    <Legend layout="horizontal" verticalAlign="bottom" align="center" wrapperStyle={{ bottom: 0, left: 20 }}/>
                    {tactics.map(tactic => (
                        <Scatter 
                            key={tactic} 
                            name={tactic} 
                            data={chartData.filter(d => d.tactic === tactic)} 
                            fill={getTacticColor(tactic)} 
                            fillOpacity={0.6}
                            shape="circle"
                            onClick={(props) => onBubbleClick(props.tactic)}
                            className="cursor-pointer"
                        />
                    ))}
                     <Brush dataKey="x" height={30} stroke="hsl(var(--primary))" />
                </ScatterChart>
            </ResponsiveContainer>
        </ChartContainer>
        <div className="text-center mt-4">
            <Button variant="link" onClick={() => onBubbleClick(null)} className="interactive-glow-0">Reset Filter</Button>
        </div>
      </CardContent>
    </Card>
  );
}
