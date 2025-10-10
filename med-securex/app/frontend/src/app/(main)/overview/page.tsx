

'use client';

import { MetricCard } from '@/components/dashboard/MetricCard';
import { AlertsOverTimeChart } from '@/components/dashboard/AlertsOverTimeChart';
import { RecentAlertsTable } from '@/components/dashboard/RecentAlertsTable';
import { AlertSourcesChart } from '@/components/dashboard/AlertSourcesChart';
import { TopSystemsChart } from '@/components/dashboard/TopSystemsChart';
import { BarChart, FileText, ShieldAlert, AlertCircle } from 'lucide-react';
import Link from 'next/link';
import { Separator } from '@/components/ui/separator';
import { MitreAttackChart } from '@/components/dashboard/MitreAttackChart';
import { AlertsEvolutionChart } from '@/components/dashboard/AlertsEvolutionChart';
import { StatisticsBar } from '@/components/dashboard/StatisticsBar';
import { cn } from '@/lib/utils';

const severityColorMap: Record<string, string> = {
  'Critical': 'bg-purple-500',
  'High': 'bg-red-500',
  'Medium': 'bg-orange-500',
  'Low': 'bg-yellow-400',
}

const DetailsList = ({ items }: { items: { label: string, value: string | number }[] }) => (
  <ul className="space-y-2 mt-2">
    {items.map(item => (
      <li key={item.label} className="flex justify-between items-center text-xs space-x-4">
        <div className="flex items-center gap-2">
          {severityColorMap[item.label] && <div className={cn("h-2 w-2 rounded-full", severityColorMap[item.label])} />}
          <span className="text-muted-foreground">{item.label}</span>
        </div>
        <span className="font-semibold">{item.value}</span>
      </li>
    ))}
  </ul>
);

export default function OverviewPage() {
  const iconGlowStyle = "text-[#2fc1a6]";

  return (
    <div className="flex-1 space-y-6">
      <div>
        <h1 className="text-3xl font-bold font-headline text-center">Overview</h1>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Link href="/alerts">
          <MetricCard
            icon={ShieldAlert}
            title="Total Alerts (24h)"
            value="1,284"
            description="+5.2% from yesterday"
            iconClassName={iconGlowStyle}
            detailsContent={<DetailsList items={[
              { label: 'Critical', value: 15 },
              { label: 'High', value: 73 },
              { label: 'Medium', value: 432 },
              { label: 'Low', value: 764 },
            ]} />}
          />
        </Link>
        <Link href="/alerts?severity=High">
          <MetricCard
            icon={AlertCircle}
            title="High Severity Alerts"
            value="73"
            description="-3.1% from yesterday"
            iconClassName={iconGlowStyle}
            detailsContent={<DetailsList items={[
              { label: 'T1110', value: 'Brute Force' },
              { label: 'T1071', value: 'Web Protocols' },
              { label: 'T1059', value: 'PowerShell' },
            ]} />}
          />
        </Link>
        <Link href="/incidents">
          <MetricCard
            icon={FileText}
            title="Open Incidents"
            value="12"
            description="2 require immediate attention"
            iconClassName={iconGlowStyle}
            detailsContent={<DetailsList items={[
              { label: 'Active', value: 3 },
              { label: 'Investigating', value: 9 },
              { label: 'Resolved', value: 58 },
            ]} />}
          />
        </Link>
        <Link href="/ttps">
          <MetricCard
            icon={BarChart}
            title="TTPs Detected"
            value="48"
            description="T1059.001 most common"
            iconClassName={iconGlowStyle}
            detailsContent={<DetailsList items={[
              { label: 'T1059.001', value: 48 },
              { label: 'T1071.001', value: 32 },
              { label: 'T1110', value: 25 },
              { label: 'T1530', value: 18 },
              { label: 'T1486', value: 15 },
            ]} />}
          />
        </Link>
      </div>

      <Separator />

      <StatisticsBar />

      <Separator />

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
        <div className="col-span-12 lg:col-span-4">
            <AlertsOverTimeChart />
        </div>
        <div className="col-span-12 lg:col-span-3">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-4 h-full mt-6 md:mt-0">
                <AlertSourcesChart />
                <MitreAttackChart />
            </div>
        </div>
      </div>
      
      <div>
        <RecentAlertsTable />
      </div>

       <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-2">
        <TopSystemsChart />
        <AlertsEvolutionChart />
      </div>

    </div>
  );
}
