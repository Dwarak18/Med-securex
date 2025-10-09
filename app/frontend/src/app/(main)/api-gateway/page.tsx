import SuricataAlerts from '@/components/api-gateway/SuricataAlerts';

export default function ApiGatewayPage() {
  return (
    <div className="flex-1 space-y-4">
      <h1 className="text-3xl font-bold font-headline text-center mb-4">
        API Gateway Security
      </h1>
      <p className="text-muted-foreground text-center">
        Live Suricata alerts from the API Gateway.
      </p>
      <div className="pt-2">
        <SuricataAlerts />
      </div>
    </div>
  );
}
