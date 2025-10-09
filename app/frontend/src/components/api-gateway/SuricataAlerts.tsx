'use client';

import { useState, useEffect, useCallback } from 'react';
import { getSuricataAlerts } from '@/app/actions';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { AlertTriangle, WifiOff, RefreshCw } from 'lucide-react';
import { Button } from '../ui/button';

interface SuricataAlert {
  timestamp: string;
  src_ip: string;
  src_port: number;
  dest_ip: string;
  dest_port: number;
  proto: string;
  alert: {
    signature: string;
    category: string;
    severity: number;
  };
}

const severityMap: Record<number, { text: string; className: string }> = {
  1: { text: 'High', className: 'bg-red-600 text-white' },
  2: { text: 'Medium', className: 'bg-orange-500 text-white' },
  3: { text: 'Low', className: 'bg-yellow-400 text-black' },
};

export default function SuricataAlerts() {
  const [alerts, setAlerts] = useState<SuricataAlert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAlerts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    const result = await getSuricataAlerts();
    if (result.data && result.data.alerts) {
      setAlerts(result.data.alerts);
    } else {
      setError(result.error || 'Failed to fetch alerts.');
      setAlerts([]);
    }
    setIsLoading(false);
  }, []);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  const renderContent = () => {
    if (isLoading && alerts.length === 0) {
      return (
        <TableBody>
          {Array.from({ length: 5 }).map((_, index) => (
            <TableRow key={index}>
              <TableCell><Skeleton className="h-4 w-32" /></TableCell>
              <TableCell><Skeleton className="h-4 w-24" /></TableCell>
              <TableCell className="hidden md:table-cell"><Skeleton className="h-4 w-48" /></TableCell>
              <TableCell className="hidden sm:table-cell"><Skeleton className="h-4 w-24" /></TableCell>
              <TableCell className="text-center"><Skeleton className="h-6 w-16 mx-auto" /></TableCell>
            </TableRow>
          ))}
        </TableBody>
      );
    }

    if (error) {
      return (
        <TableBody>
          <TableRow>
            <TableCell colSpan={5}>
              <div className="flex flex-col items-center justify-center text-center py-12">
                <WifiOff className="h-12 w-12 text-destructive mb-4" />
                <h3 className="text-xl font-semibold text-destructive">Connection Error</h3>
                <p className="text-muted-foreground mt-2 max-w-md">{error}</p>
                <Button onClick={fetchAlerts} className="mt-6">
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Retry Connection
                </Button>
              </div>
            </TableCell>
          </TableRow>
        </TableBody>
      );
    }

    if (alerts.length === 0) {
      return (
        <TableBody>
          <TableRow>
            <TableCell colSpan={5} className="h-24 text-center">
              No Suricata alerts found. The gateway is connected, but there's no threat data to display.
            </TableCell>
          </TableRow>
        </TableBody>
      );
    }

    return (
      <TableBody>
        {alerts.map((alert, index) => (
          <TableRow key={`${alert.timestamp}-${index}`}>
            <TableCell>{new Date(alert.timestamp).toLocaleString()}</TableCell>
            <TableCell className="font-mono">{alert.src_ip}:{alert.src_port}</TableCell>
            <TableCell className="hidden md:table-cell">{alert.alert.signature}</TableCell>
            <TableCell className="hidden sm:table-cell">{alert.alert.category}</TableCell>
            <TableCell className="text-center">
              <Badge className={severityMap[alert.alert.severity]?.className || 'bg-gray-400'}>
                {severityMap[alert.alert.severity]?.text || 'Info'}
              </Badge>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    );
  };

  return (
    <Card className="rounded-2xl shadow-lg">
      <CardHeader>
        <CardTitle>Suricata IDS/IPS Alerts</CardTitle>
        <CardDescription>
          Real-time threat detection from the network intrusion detection system. Refreshes automatically.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="border rounded-lg">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Source</TableHead>
                <TableHead className="hidden md:table-cell">Signature</TableHead>
                <TableHead className="hidden sm:table-cell">Category</TableHead>
                <TableHead className="text-center">Severity</TableHead>
              </TableRow>
            </TableHeader>
            {renderContent()}
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}
