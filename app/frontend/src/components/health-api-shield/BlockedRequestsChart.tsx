'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { AreaChart, Area, XAxis } from 'recharts';

const chartConfig = {
  blocked: {
    label: 'Blocked',
    color: 'hsl(var(--destructive))',
  },
};

export function BlockedRequestsChart() {
  const [chartData, setChartData] = useState<Array<{ blocked: number }>>([]);

  useEffect(() => {
    // This log will confirm the variable is being read in the browser
    console.log('API URL from Vercel env:', process.env.NEXT_PUBLIC_API_URL);

    const fetchData = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        
        if (apiUrl) {
          const response = await fetch(`${apiUrl}/api/blocked-requests`);
          const data = await response.json();
          setChartData(data);
        } else {
          console.error('ERROR: API URL is not defined. Double-check Vercel environment variables.');
        }
      } catch (error) {
        console.error("Failed to fetch blocked requests data:", error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  const totalBlocked = Array.isArray(chartData)
    ? chartData.reduce((sum, item) => sum + (typeof item.blocked === 'number' ? item.blocked : 0), 0)
    : 0;

  return (
    <Card className="rounded-2xl shadow-lg">
      <CardHeader>
        <CardTitle>Blocked Requests</CardTitle>
        <CardDescription>Threats blocked in real-time.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="text-4xl font-bold text-destructive">{totalBlocked.toLocaleString()}</div>
        <p className="text-xs text-muted-foreground">+15.2% from last hour</p>
        <div className="h-32 mt-4">
          <ChartContainer config={chartConfig}>
            <AreaChart accessibilityLayer data={chartData} margin={{ left: 0, right: 0, top: 0, bottom: 0 }}>
              <defs>
                <linearGradient id="fillBlocked" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="var(--color-blocked)" stopOpacity={0.8} />
                  <stop offset="95%" stopColor="var(--color-blocked)" stopOpacity={0.1} />
                </linearGradient>
              </defs>
              <XAxis dataKey="time" hide />
              <ChartTooltip cursor={false} content={<ChartTooltipContent indicator="line" />} />
              <Area dataKey="blocked" type="natural" fill="url(#fillBlocked)" stroke="var(--color-blocked)" stackId="a" />
            </AreaChart>
          </ChartContainer>
        </div>
      </CardContent>
    </Card>
  );
}
