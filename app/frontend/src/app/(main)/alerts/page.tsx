import { AlertsTable } from '@/components/alerts/AlertsTable';

export default function AlertsPage() {
  return (
    <div className="flex-1 space-y-4">
      <h1 className="text-3xl font-bold font-headline text-center mb-4">Alerts</h1>
      <p className="text-muted-foreground text-center">
        Investigate, filter, and analyze security alerts from all connected sources.
      </p>
      <div className="pt-2">
        <AlertsTable />
      </div>
    </div>
  );
}
