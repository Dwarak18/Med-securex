'use client';

import * as React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { PieChart, Pie, Cell, Tooltip } from 'recharts';
import type { IncidentStatus } from '@/types';

interface IncidentStatusChartProps {
    data: Record<IncidentStatus, number>;
}

const chartConfig = {
    'Open': { label: 'Open', color: 'hsl(var(--destructive))' },
    'In Progress': { label: 'In Progress', color: 'hsl(var(--primary))' },
    'Resolved': { label: 'Resolved', color: 'hsl(var(--chart-2))' },
    'Closed': { label: 'Closed', color: 'hsl(var(--muted))' },
};

export function IncidentStatusChart({ data }: IncidentStatusChartProps) {
    const [activeIndex, setActiveIndex] = React.useState<number | null>(null);
    
    const chartData = Object.entries(data).map(([status, count]) => ({
        status,
        count,
        fill: chartConfig[status as IncidentStatus]?.color || '#888888'
    }));

    const totalIncidents = React.useMemo(() => {
        return chartData.reduce((acc, curr) => acc + curr.count, 0);
    }, [chartData]);
    
    const onPieEnter = (_: any, index: number) => {
        setActiveIndex(index);
    };

    const onPieLeave = () => {
        setActiveIndex(null);
    };

    return (
        <Card className="rounded-2xl shadow-lg h-full flex flex-col">
            <CardHeader className="items-center pb-0">
                <CardTitle>Incidents by Status</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 pb-0">
                <ChartContainer
                    config={chartConfig}
                    className="mx-auto aspect-square h-full"
                >
                    <PieChart>
                        <ChartTooltip
                            cursor={false}
                            content={<ChartTooltipContent hideLabel />}
                        />
                        <Pie
                            data={chartData}
                            dataKey="count"
                            nameKey="status"
                            innerRadius={50}
                            strokeWidth={0}
                            onMouseEnter={onPieEnter}
                            onMouseLeave={onPieLeave}
                        >
                            {chartData.map((entry, index) => (
                                <Cell 
                                    key={`cell-${entry.status}`} 
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
            </CardContent>
            <div className="flex-1 p-4 text-center text-sm text-muted-foreground">
                Total: {totalIncidents} incidents
            </div>
        </Card>
    );
}
