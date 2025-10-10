'use client';

import { useMemo, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import type { Alert } from '@/types';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { StatusBadge } from '../ui/StatusBadge';

const recentAlerts: Alert[] = [
  { id: 'AL-9876', timestamp: '2023-10-27 14:45:12', severity: 'Critical', description: 'Ransomware behavior detected on endpoint SRV-DB01', ttp_id: 'T1486', status: 'New', source: 'EDR', entity: 'SRV-DB01' },
  { id: 'AL-9875', timestamp: '2023-10-27 14:30:05', severity: 'High', description: 'Unusual outbound traffic to known C2 server', ttp_id: 'T1071', status: 'In Progress', source: 'Firewall', entity: 'PC-MKTG-05' },
  { id: 'AL-9871', timestamp: '2023-10-26 20:05:33', severity: 'Critical', description: 'Data exfiltration from patient DB', ttp_id: 'T1048', status: 'New', source: 'DLP', entity: 'DB-PATIENT-RECORDS' },
  { id: 'AL-9874', timestamp: '2023-10-27 13:55:41', severity: 'High', description: 'Multiple failed login attempts for admin account', ttp_id: 'T1110', status: 'Resolved', source: 'Active Directory', entity: 'admin' },
  { id: 'AL-9872', timestamp: '2023-10-26 22:10:19', severity: 'High', description: 'PowerShell execution with suspicious arguments', ttp_id: 'T1059.001', status: 'Resolved', source: 'EDR', entity: 'SRV-WEB02' },
];

const severityStyles: Record<Alert['severity'], string> = {
  Critical: 'bg-purple-700 text-white border-transparent',
  High: 'bg-red-600 text-white border-transparent',
  Medium: 'bg-orange-500 text-white border-transparent',
  Low: 'bg-yellow-400 text-black border-transparent',
};

export function RecentAlertsTable() {
  const [severityFilter, setSeverityFilter] = useState('all');
  const [statusFilter, setStatusFilter] = useState('all');

  const filteredAlerts = useMemo(() => {
    return recentAlerts.filter(alert => {
      const severityMatch = severityFilter === 'all' || alert.severity === severityFilter;
      const statusMatch = statusFilter === 'all' || alert.status === statusFilter;
      return severityMatch && statusMatch;
    });
  }, [severityFilter, statusFilter]);

  return (
    <Card className="rounded-2xl shadow-lg">
      <CardHeader>
        <div className="flex flex-col md:flex-row justify-between md:items-center gap-4">
            <div className='flex-1'>
                <CardTitle>Recent High-Severity Alerts</CardTitle>
                <CardDescription>A summary of the latest critical and high-priority threats.</CardDescription>
            </div>
            <div className="flex flex-col sm:flex-row gap-2">
                <Select value={severityFilter} onValueChange={setSeverityFilter}>
                <SelectTrigger className="w-full sm:w-[160px]">
                    <SelectValue placeholder="Filter by severity" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="all">All Severities</SelectItem>
                    <SelectItem value="Critical">Critical</SelectItem>
                    <SelectItem value="High">High</SelectItem>
                    <SelectItem value="Medium">Medium</SelectItem>
                    <SelectItem value="Low">Low</SelectItem>
                </SelectContent>
                </Select>
                <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-full sm:w-[160px]">
                    <SelectValue placeholder="Filter by status" />
                </SelectTrigger>
                <SelectContent>
                    <SelectItem value="all">All Statuses</SelectItem>
                    <SelectItem value="New">New</SelectItem>
                    <SelectItem value="In Progress">In Progress</SelectItem>
                    <SelectItem value="Resolved">Resolved</SelectItem>
                    <SelectItem value="Dismissed">Dismissed</SelectItem>
                </SelectContent>
                </Select>
            </div>
        </div>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-center">Severity</TableHead>
              <TableHead>Description</TableHead>
              <TableHead className="text-center">Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {filteredAlerts.length > 0 ? (
                filteredAlerts.map((alert) => (
                <TableRow key={alert.id}>
                    <TableCell className="text-center">
                      <Badge className={severityStyles[alert.severity]}>{alert.severity}</Badge>
                    </TableCell>
                    <TableCell className="font-medium">{alert.description}</TableCell>
                    <TableCell className="text-center">
                      <StatusBadge status={alert.status} />
                    </TableCell>
                </TableRow>
                ))
            ) : (
                <TableRow>
                    <TableCell colSpan={3} className="text-center h-24">
                        No alerts match the current filters.
                    </TableCell>
                </TableRow>
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
