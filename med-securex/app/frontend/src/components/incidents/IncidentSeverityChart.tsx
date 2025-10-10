'use client';

import { Bar, BarChart, CartesianGrid, XAxis, YAxis, Cell } from 'recharts';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import type { IncidentSeverity } from '@/types';

interface IncidentSeverityChartProps {
    data: Record<IncidentSeverity, number>;
}

const chartConfig = {
    count: { label: 'Count' },
    'Critical': { label: 'Critical', color: 'hsl(var(--chart-5))' },
    'High': { label: 'High', color: 'hsl(var(--destructive))' },
    'Medium': { label: 'Medium', color: 'hsl(var(--primary))' },
    'Low': { label: 'Low', color: 'hsl(var(--chart-2))' },
};

export function IncidentSeverityChart({ data }: IncidentSeverityChartProps) {
    const chartData = Object.entries(data).map(([severity, count]) => ({
        severity,
        count,
    }));

    return (
        <Card className="rounded-2xl shadow-lg h-full">
            <CardHeader className="items-center pb-0">
                <CardTitle>Incidents by Severity</CardTitle>
            </CardHeader>
            <CardContent>
                <ChartContainer config={chartConfig} className="h-[180px] w-full">
                    <BarChart
                        accessibilityLayer
                        data={chartData}
                        layout="vertical"
                        margin={{ left: 10, right: 10, top: 10, bottom: 10 }}
                    >
                        <CartesianGrid horizontal={false} />
                        <YAxis
                            dataKey="severity"
                            type="category"
                            tickLine={false}
                            tickMargin={10}
                            axisLine={false}
                            tickFormatter={(value) => value.slice(0, 3)}
                        />
                        <XAxis dataKey="count" type="number" hide />
                        <ChartTooltip
                            cursor={false}
                            content={<ChartTooltipContent indicator="line" />}
                        />
                        <Bar
                            dataKey="count"
                            layout="vertical"
                            radius={5}
                        >
                            {chartData.map((entry) => (
                                <Cell key={entry.severity} fill={chartConfig[entry.severity as IncidentSeverity]?.color || '#888888'} />
                            ))}
                        </Bar>
                    </BarChart>
                </ChartContainer>
            </CardContent>
        </Card>
    );
}
