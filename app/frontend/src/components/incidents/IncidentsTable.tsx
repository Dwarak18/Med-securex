'use client';

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { StatusBadge } from '../ui/StatusBadge';
import type { Incident, IncidentSeverity } from '@/types';

interface IncidentsTableProps {
  incidents: Incident[];
}

const severityStyles: Record<IncidentSeverity, string> = {
  Critical: 'bg-purple-700 text-white border-transparent',
  High: 'bg-red-600 text-white border-transparent',
  Medium: 'bg-orange-500 text-white border-transparent',
  Low: 'bg-yellow-400 text-black border-transparent',
};

export function IncidentsTable({ incidents }: IncidentsTableProps) {
  return (
    <Card className="rounded-2xl shadow-lg">
        <CardHeader>
            <CardTitle>All Incidents</CardTitle>
            <CardDescription>A complete log of all open and historical security incidents.</CardDescription>
        </CardHeader>
        <CardContent>
            <Table>
                <TableHeader>
                <TableRow>
                    <TableHead className="text-center">ID</TableHead>
                    <TableHead>Title</TableHead>
                    <TableHead className="text-center">Status</TableHead>
                    <TableHead className="text-center">Severity</TableHead>
                    <TableHead className="text-center">Assignee</TableHead>
                    <TableHead className="text-center">Created</TableHead>
                </TableRow>
                </TableHeader>
                <TableBody>
                {incidents.map((incident) => (
                    <TableRow key={incident.id}>
                    <TableCell className="font-mono text-center">{incident.id}</TableCell>
                    <TableCell className="font-medium">{incident.title}</TableCell>
                    <TableCell className="text-center">
                        <StatusBadge status={incident.status} />
                    </TableCell>
                    <TableCell className="text-center">
                        <Badge className={severityStyles[incident.severity]}>{incident.severity}</Badge>
                    </TableCell>
                    <TableCell className="text-center">{incident.assignee}</TableCell>
                    <TableCell className="text-center">{new Date(incident.created).toLocaleString()}</TableCell>
                    </TableRow>
                ))}
                </TableBody>
            </Table>
        </CardContent>
    </Card>
  );
}
