import { ApiUsageChart } from '@/components/health-api-shield/ApiUsageChart';
import { BlockedRequestsChart } from '@/components/health-api-shield/BlockedRequestsChart';
import { PiiScrubbingReportChart } from '@/components/health-api-shield/PiiScrubbingReportChart';
import { ShieldAlertsTable } from '@/components/health-api-shield/ShieldAlertsTable';

export default function HealthApiShieldPage() {
  return (
    <div className="flex-1">
      <h1 className="text-3xl font-bold font-headline text-center mb-6">Health API Shield</h1>
      <div className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <ApiUsageChart />
          </div>
          <BlockedRequestsChart />
        </div>
        <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-1">
          <PiiScrubbingReportChart />
        </div>
        <div className="grid gap-6">
          <ShieldAlertsTable />
        </div>
      </div>
    </div>
  );
}
