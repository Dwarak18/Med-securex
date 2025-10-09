'use client';

import { useEffect, useState } from 'react';
import { type Alert } from '@/types';
import { getTtpCorrelation } from '@/app/actions';
import type { CorrelateAlertsTTPOutput } from '@/ai/flows/correlate-alerts-ttp';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Skeleton } from '@/components/ui/skeleton';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Bot } from 'lucide-react';
import { StatusBadge } from '../ui/StatusBadge';

interface AlertDetailsProps {
  alert: Alert;
}

const severityStyles: Record<Alert['severity'], string> = {
  Critical: 'bg-purple-700 text-white border-transparent',
  High: 'bg-red-600 text-white border-transparent',
  Medium: 'bg-orange-500 text-white border-transparent',
  Low: 'bg-yellow-400 text-black border-transparent',
};

export function AlertDetails({ alert }: AlertDetailsProps) {
  const [correlation, setCorrelation] = useState<CorrelateAlertsTTPOutput | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCorrelation = async () => {
    setIsLoading(true);
    setError(null);
    const result = await getTtpCorrelation({ ttp_id: alert.ttp_id, alertDescription: alert.description });
    if (result.data) {
      setCorrelation(result.data);
    } else {
      setError(result.error);
    }
    setIsLoading(false);
  };
  
  useEffect(() => {
    handleCorrelation();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [alert.id]);

  return (
    <div className="space-y-6 p-1">
      <Card>
        <CardHeader>
          <CardTitle>Alert Details</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div><span className="font-semibold">Alert ID:</span> {alert.id}</div>
            <div><span className="font-semibold">Timestamp:</span> {new Date(alert.timestamp).toLocaleString()}</div>
            <div><span className="font-semibold">Entity:</span> {alert.entity}</div>
            <div><span className="font-semibold">Source:</span> {alert.source}</div>
            <div><span className="font-semibold">Severity:</span> <Badge className={severityStyles[alert.severity]}>{alert.severity}</Badge></div>
            <div><span className="font-semibold">Status:</span> <StatusBadge status={alert.status} /></div>
          </div>
          <div>
            <div className="font-semibold">Description:</div>
            <p className="text-muted-foreground">{alert.description}</p>
          </div>
        </CardContent>
      </Card>

      <Separator />

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <div className="flex items-center gap-2">
            <Bot className="h-6 w-6 text-primary" />
            <CardTitle>AI Threat Correlation</CardTitle>
          </div>
          <Button variant="ghost" size="sm" onClick={handleCorrelation} disabled={isLoading}>
            {isLoading ? 'Analyzing...' : 'Re-analyze'}
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading && (
            <div className="space-y-4">
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-4 w-full" />
              <Skeleton className="h-4 w-3/4" />
              <Skeleton className="h-4 w-1/2" />
            </div>
          )}
          {error && (
            <div className="text-destructive flex items-center gap-2">
              <AlertTriangle className="h-5 w-5" />
              <div>
                <p className="font-semibold">Error analyzing TTP</p>
                <p className="text-sm">{error}</p>
              </div>
            </div>
          )}
          {correlation && !isLoading && !error && (
            <div className="space-y-4">
              <div>
                <h4 className="font-semibold text-lg">Threat: {correlation.threatName}</h4>
              </div>
              <div>
                <h4 className="font-semibold">Potential Impact</h4>
                <p className="text-muted-foreground">{correlation.impactAssessment}</p>
              </div>
              <div>
                <h4 className="font-semibold">Associated MITRE ATT&CK Techniques</h4>
                <div className="flex flex-wrap gap-2 mt-2">
                  {correlation.mitreTechniques.map((technique) => (
                    <Badge key={technique} variant="secondary">{technique}</Badge>
                  ))}
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
