'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { BarChart, Bar, CartesianGrid, XAxis, YAxis, Legend } from 'recharts';

const chartData = [
  { policy: 'Patient Confidentiality', violations: 45 },
  { policy: 'Financial Data', violations: 22 },
  { policy: 'HIPAA', violations: 78 },
  { policy: 'GDPR', violations: 12 },
  { policy: 'Employee PII', violations: 31 },
];

const chartConfig = {
  violations: {
    label: 'Violations',
    color: 'hsl(var(--destructive))',
  },
};

export function DlpViolationsChart() {
  return (
    <Card className="rounded-2xl shadow-lg h-full">
      <CardHeader>
        <CardTitle>DLP Violations</CardTitle>
        <CardDescription>Top data loss prevention policies violated.</CardDescription>
      </CardHeader>
      <CardContent>
        <ChartContainer config={chartConfig} className="h-[250px] w-full">
          <BarChart layout="vertical" data={chartData} margin={{ top: 5, right: 20, left: 10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={false} />
            <XAxis type="number" />
            <YAxis dataKey="policy" type="category" width={110} tickLine={false} axisLine={false} />
            <ChartTooltip content={<ChartTooltipContent />} />
            <Legend />
            <Bar dataKey="violations" fill="var(--color-violations)" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ChartContainer>
      </CardContent>
    </Card>
  );
}
