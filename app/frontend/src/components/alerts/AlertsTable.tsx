'use client';

import { useState, useMemo, useEffect } from 'react';
import type { Alert, AlertSeverity, AlertStatus } from '@/types';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from '@/components/ui/sheet';
import { AlertDetails } from './AlertDetails';
import { ArrowUpDown, Search } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { StatusBadge } from '../ui/StatusBadge';
import { getAlerts } from '@/app/actions';
import { useToast } from '@/hooks/use-toast';
import { Skeleton } from '../ui/skeleton';

const severityOrder: Record<AlertSeverity, number> = { 'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1 };
const severityStyles: Record<Alert['severity'], string> = {
  Critical: 'bg-purple-700 text-white border-transparent',
  High: 'bg-red-600 text-white border-transparent',
  Medium: 'bg-orange-500 text-white border-transparent',
  Low: 'bg-yellow-400 text-black border-transparent',
};


export function AlertsTable() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('all');
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [sortConfig, setSortConfig] = useState<{ key: keyof Alert; direction: 'ascending' | 'descending' } | null>({ key: 'timestamp', direction: 'descending' });
  const { toast } = useToast();

  useEffect(() => {
    async function loadAlerts() {
        setIsLoading(true);
        const { data, error } = await getAlerts();
        if (error) {
            toast({ variant: 'destructive', title: 'Failed to load alerts', description: error });
            setAlerts([]);
        } else {
            setAlerts(data || []);
        }
        setIsLoading(false);
    }
    loadAlerts();
  }, [toast]);
  
  const filteredAlerts = useMemo(() => {
    let filtered = alerts.filter(alert =>
      alert.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      alert.ttp_id.toLowerCase().includes(searchTerm.toLowerCase())
    );
    if (severityFilter !== 'all') {
      filtered = filtered.filter(alert => alert.severity === severityFilter);
    }
    if (statusFilter !== 'all') {
      filtered = filtered.filter(alert => alert.status === statusFilter);
    }
    return filtered;
  }, [alerts, searchTerm, severityFilter, statusFilter]);

  const sortedAlerts = useMemo(() => {
    let sortableItems = [...filteredAlerts];
    if (sortConfig !== null) {
      sortableItems.sort((a, b) => {
        let aValue = a[sortConfig.key];
        let bValue = b[sortConfig.key];
        
        if (sortConfig.key === 'severity') {
          aValue = severityOrder[a.severity];
          bValue = severityOrder[b.severity];
        }

        if (aValue < bValue) {
          return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (aValue > bValue) {
          return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  }, [filteredAlerts, sortConfig]);

  const requestSort = (key: keyof Alert) => {
    let direction: 'ascending' | 'descending' = 'ascending';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  const renderTableBody = () => {
    if (isLoading) {
        return (
            <TableBody>
                {Array.from({length: 5}).map((_, i) => (
                    <TableRow key={i}>
                        <TableCell><Skeleton className="h-6 w-20" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-full" /></TableCell>
                        <TableCell className="hidden md:table-cell"><Skeleton className="h-4 w-24" /></TableCell>
                        <TableCell className="hidden sm:table-cell"><Skeleton className="h-6 w-24" /></TableCell>
                        <TableCell><Skeleton className="h-4 w-32" /></TableCell>
                    </TableRow>
                ))}
            </TableBody>
        )
    }
    if (sortedAlerts.length === 0) {
        return (
            <TableBody>
                <TableRow>
                    <TableCell colSpan={5} className="h-24 text-center">No alerts found.</TableCell>
                </TableRow>
            </TableBody>
        )
    }
    return (
        <TableBody>
          {sortedAlerts.map((alert) => (
            <TableRow key={alert.id} onClick={() => setSelectedAlert(alert)} className="cursor-pointer">
              <TableCell className="text-center">
                <Badge className={severityStyles[alert.severity]}>
                  {alert.severity}
                </Badge>
              </TableCell>
              <TableCell className="font-medium">{alert.description}</TableCell>
              <TableCell className="hidden md:table-cell text-center"><Badge variant="outline">{alert.ttp_id}</Badge></TableCell>
              <TableCell className="hidden sm:table-cell text-center"><StatusBadge status={alert.status} /></TableCell>
              <TableCell className="text-center">{new Date(alert.timestamp).toLocaleString()}</TableCell>
            </TableRow>
          ))}
        </TableBody>
    );
  }

  return (
    <Sheet open={!!selectedAlert} onOpenChange={(isOpen) => !isOpen && setSelectedAlert(null)}>
      <div className="space-y-4">
        <div className="flex flex-col md:flex-row gap-4 justify-between">
          <div className="relative flex-1 md:max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
            <Input
              placeholder="Search by description or TTP ID..."
              className="pl-10"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <div className="flex flex-col sm:flex-row gap-4">
            <Select value={severityFilter} onValueChange={setSeverityFilter}>
              <SelectTrigger className="w-full sm:w-[180px]">
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
              <SelectTrigger className="w-full sm:w-[180px]">
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

        <div className="border rounded-2xl shadow-lg bg-card">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="text-center">
                  <Button variant="ghost" onClick={() => requestSort('severity')}>
                    Severity <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead>
                  <Button variant="ghost" onClick={() => requestSort('description')}>
                    Description <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead className="hidden md:table-cell text-center">TTP ID</TableHead>
                <TableHead className="hidden sm:table-cell text-center">
                  <Button variant="ghost" onClick={() => requestSort('status')}>
                    Status <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead className="text-center">
                   <Button variant="ghost" onClick={() => requestSort('timestamp')}>
                    Timestamp <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
              </TableRow>
            </TableHeader>
            {renderTableBody()}
          </Table>
        </div>
      </div>
      <SheetContent className="sm:max-w-2xl w-full p-0">
          <SheetHeader className="p-6 border-b">
              <SheetTitle>Alert Investigation</SheetTitle>
          </SheetHeader>
          <div className="overflow-y-auto h-[calc(100vh-4.5rem)]">
            {selectedAlert && <AlertDetails alert={selectedAlert} />}
          </div>
      </SheetContent>
    </Sheet>
  );
}
