'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { AreaChart, Area, CartesianGrid, XAxis, YAxis, Legend } from 'recharts';

const chartConfig = {
  rps: {
    label: 'Total Requests',
    color: 'hsl(var(--chart-1))',
  },
  success: {
    label: 'Success',
    color: 'hsl(var(--chart-2))',
  },
  errors: {
    label: 'Blocked',
    color: 'hsl(var(--destructive))',
  },
};

export function ApiUsageChart() {
  const [chartData, setChartData] = useState([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        if (apiUrl) {
          const response = await fetch(`${apiUrl}/api/api-usage`);
          const data = await response.json();
          setChartData(data);
        } else {
          console.error('ERROR: NEXT_PUBLIC_API_URL is not defined.');
        }
      } catch (error) {
        console.error("Failed to fetch API usage data:", error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  return (
    <Card className="rounded-2xl shadow-lg">
      <CardHeader>
        <CardTitle>API Usage</CardTitle>
        <CardDescription>Real-time requests, success, and error rates (last hour).</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[350px] w-full">
          <AreaChart data={chartData} margin={{ top: 5, right: 20, left: -10, bottom: 5 }}>
            <defs>
              <linearGradient id="fillRps" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-rps)" stopOpacity={0.8} />
                <stop offset="95%" stopColor="var(--color-rps)" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="fillSuccess" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-success)" stopOpacity={0.8} />
                <stop offset="95%" stopColor="var(--color-success)" stopOpacity={0.1} />
              </linearGradient>
              <linearGradient id="fillErrors" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="var(--color-errors)" stopOpacity={0.8} />
                <stop offset="95%" stopColor="var(--color-errors)" stopOpacity={0.1} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="time" tickLine={false} axisLine={false} tickMargin={8} />
            <YAxis yAxisId="left" tickLine={false} axisLine={false} tickMargin={8} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Legend />
            <Area yAxisId="left" type="monotone" dataKey="rps" stroke="var(--color-rps)" fill="url(#fillRps)" strokeWidth={2} dot={false} />
            <Area yAxisId="left" type="monotone" dataKey="success" stroke="var(--color-success)" fill="url(#fillSuccess)" strokeWidth={2} dot={false} />
            <Area yAxisId="left" type="monotone" dataKey="errors" stroke="var(--color-errors)" fill="url(#fillErrors)" strokeWidth={2} dot={false} />
          </AreaChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
