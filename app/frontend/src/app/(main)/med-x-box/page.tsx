import { TrafficStatsChart } from '@/components/med-x-box/TrafficStatsChart';
import { TopBlockedTable } from '@/components/med-x-box/TopBlockedTable';
import { ThreatMap } from '@/components/med-x-box/ThreatMap';
import { BoxAlertsTable } from '@/components/med-x-box/BoxAlertsTable';
import { DlpViolationsChart } from '@/components/med-x-box/DlpViolationsChart';

export default function MedXBoxPage() {
  return (
    <div className="flex-1">
      <h1 className="text-3xl font-bold font-headline text-center mb-6">MED x Box</h1>
      <div className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <TrafficStatsChart />
          </div>
          <div className="lg:col-span-2">
            <TopBlockedTable />
          </div>
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-5">
          <div className="lg:col-span-3">
              <ThreatMap />
          </div>
          <div className="lg:col-span-2">
              <DlpViolationsChart />
          </div>
        </div>
        <div className="grid gap-6">
          <BoxAlertsTable />
        </div>
      </div>
    </div>
  );
}
