import { PiiOverTimeChart } from '@/components/pii-reports/PiiOverTimeChart';
import { TopPiiTypesTable } from '@/components/pii-reports/TopPiiTypesTable';

export default function PiiReportsPage() {
  return (
    <div className="flex-1">
      <h1 className="text-3xl font-bold font-headline text-center mb-6">PII Reports</h1>
      <div className="space-y-6">
        <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-5">
          <div className="lg:col-span-3">
            <PiiOverTimeChart />
          </div>
          <div className="lg:col-span-2">
            <TopPiiTypesTable />
          </div>
        </div>
      </div>
    </div>
  );
}
