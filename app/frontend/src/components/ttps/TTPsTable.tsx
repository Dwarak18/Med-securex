'use client';

import { useState, useMemo, useEffect } from 'react';
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
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { ArrowUpDown, Search, X, ShieldCheck } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogClose } from '@/components/ui/dialog';
import type { TTP } from '@/types';
import { cn } from '@/lib/utils';
import { Skeleton } from '@/components/ui/skeleton';

const tacticColors: Record<string, string> = {
  'Initial Access': 'bg-green-500/20 text-green-500 border-green-500/30',
  'Execution': 'bg-yellow-500/20 text-yellow-500 border-yellow-500/30',
  'Persistence': 'bg-orange-500/20 text-orange-500 border-orange-500/30',
  'Credential Access': 'bg-red-500/20 text-red-500 border-red-500/30',
  'Collection': 'bg-blue-500/20 text-blue-500 border-blue-500/30',
  'Command and Control': 'bg-indigo-500/20 text-indigo-500 border-indigo-500/30',
  'Impact': 'bg-purple-500/20 text-purple-500 border-purple-500/30',
  'Privilege Escalation': 'bg-pink-500/20 text-pink-500 border-pink-500/30',
  'Defense Evasion': 'bg-teal-500/20 text-teal-500 border-teal-500/30',
  'Discovery': 'bg-cyan-500/20 text-cyan-500 border-cyan-500/30',
  'Lateral Movement': 'bg-lime-500/20 text-lime-500 border-lime-500/30',
  'Exfiltration': 'bg-fuchsia-500/20 text-fuchsia-500 border-fuchsia-500/30',
  'Malware': 'bg-rose-500/20 text-rose-500 border-rose-500/30',
  'Exploit': 'bg-amber-500/20 text-amber-500 border-amber-500/30',
  'Phishing': 'bg-violet-500/20 text-violet-500 border-violet-500/30',
  'Brute Force': 'bg-red-700/20 text-red-700 border-red-700/30'
};


interface TTPsTableProps {
    ttps: TTP[];
    selectedTactic: string | null;
}

export function TTPsTable({ ttps, selectedTactic }: TTPsTableProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [sortConfig, setSortConfig] = useState<{ key: keyof TTP; direction: 'ascending' | 'descending' } | null>({ key: 'count', direction: 'descending' });
  const [selectedTtp, setSelectedTtp] = useState<TTP | null>(null);

  const filteredAndSortedTTPs = useMemo(() => {
    let filtered = ttps.filter(ttp => {
        const searchMatch = ttp.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (ttp.name && ttp.name.toLowerCase().includes(searchTerm.toLowerCase())) ||
            ttp.tactic.toLowerCase().includes(searchTerm.toLowerCase());
        const tacticMatch = selectedTactic ? ttp.tactic === selectedTactic : true;
        return searchMatch && tacticMatch;
    });

    if (sortConfig !== null) {
      filtered.sort((a, b) => {
        const aVal = a[sortConfig.key];
        const bVal = b[sortConfig.key];
        if (aVal < bVal) {
          return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (aVal > bVal) {
          return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
      });
    }
    
    return filtered;
  }, [ttps, searchTerm, sortConfig, selectedTactic]);

  const requestSort = (key: keyof TTP) => {
    let direction: 'ascending' | 'descending' = 'ascending';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };
  
  const handleRowClick = (ttp: TTP) => {
    setSelectedTtp(ttp);
  };

  return (
    <>
      <Card className="rounded-2xl shadow-lg">
        <CardHeader>
          <CardTitle className="text-center">TTPs Detected</CardTitle>
          <CardDescription className="text-center">MITRE ATT&amp;CK techniques observed in your environment.</CardDescription>
        </CardHeader>
        <div className="py-4 px-6">
          <div className="relative w-full max-w-md mx-auto">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                placeholder="Search by ID, Name, or Tactic..."
                className="pl-10 rounded-2xl border-border focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-0 transition duration-200 ease-in-out"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
          </div>
        </div>
        <CardContent className="pt-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="hidden md:table-cell text-center">ID</TableHead>
                <TableHead>Name</TableHead>
                <TableHead className="hidden sm:table-cell text-center">Tactic</TableHead>
                <TableHead className="text-center">
                  <Button variant="ghost" onClick={() => requestSort('count')}>
                    Count
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
                <TableHead className="hidden lg:table-cell text-center">
                  <Button variant="ghost" onClick={() => requestSort('lastSeen')}>
                    Last Seen
                    <ArrowUpDown className="ml-2 h-4 w-4" />
                  </Button>
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredAndSortedTTPs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} className="h-24 text-center">
                    No TTPs found.
                  </TableCell>
                </TableRow>
              ) : (
                filteredAndSortedTTPs.map((ttp) => (
                  <TableRow key={ttp.id} onClick={() => handleRowClick(ttp)} className="cursor-pointer">
                    <TableCell className="font-mono hidden md:table-cell text-center">{ttp.id}</TableCell>
                    <TableCell className="font-medium">{ttp.name}</TableCell>
                    <TableCell className="hidden sm:table-cell text-center">
                      <Badge className={cn("border", tacticColors[ttp.tactic] || 'bg-gray-500/20 text-gray-500 border-gray-500/30')}>{ttp.tactic}</Badge>
                    </TableCell>
                    <TableCell className="text-center">{ttp.count}</TableCell>
                    <TableCell className="hidden lg:table-cell text-center">{new Date(ttp.lastSeen).toLocaleString()}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
      
      <Dialog open={!!selectedTtp} onOpenChange={() => setSelectedTtp(null)}>
        <DialogContent className="sm:max-w-2xl bg-card text-card-foreground rounded-2xl shadow-2xl">
          {selectedTtp && (
            <>
                <DialogHeader>
                    <DialogTitle className="text-2xl font-headline">{selectedTtp.id}: {selectedTtp.name}</DialogTitle>
                </DialogHeader>
                <div className="py-4 space-y-6 max-h-[70vh] overflow-y-auto px-1">
                    <div className="space-y-2">
                        <h3 className="font-semibold text-lg">Tactic</h3>
                        <Badge className={cn("border", tacticColors[selectedTtp.tactic] || 'bg-gray-500/20 text-gray-500 border-gray-500/30')}>{selectedTtp.tactic}</Badge>
                    </div>
                    <div className="space-y-2">
                        <h3 className="font-semibold text-lg">Description</h3>
                        <p className="text-muted-foreground">{selectedTtp.description}</p>
                    </div>
                    <div className="space-y-2">
                        <h3 className="font-semibold text-lg">Detection Signature</h3>
                        <p className="text-muted-foreground font-mono bg-muted/50 p-2 rounded-md">{selectedTtp.source}</p>
                    </div>
                     <div className="space-y-2">
                        <h3 className="font-semibold text-lg">Example Payload</h3>
                        <p className="text-muted-foreground font-mono bg-muted/50 p-2 rounded-md">{selectedTtp.endpoint}</p>
                    </div>
                    <div className="space-y-2">
                        <h3 className="font-semibold text-lg">Last Seen</h3>
                        <p className="text-muted-foreground">{new Date(selectedTtp.lastSeen).toLocaleString()}</p>
                    </div>
                    <div className="space-y-2 pt-4">
                        <h3 className="font-semibold text-lg flex items-center gap-2"><ShieldCheck className="text-primary"/> How to Respond</h3>
                        <div className="p-4 bg-background/50 rounded-lg border text-sm text-muted-foreground">
                            <p><strong>1. Isolate:</strong> Immediately isolate the affected endpoint from the network to prevent lateral movement.</p>
                            <p><strong>2. Investigate:</strong> Analyze logs from the source and endpoint to determine the scope of the attack.</p>
                            <p><strong>3. Remediate:</strong> Remove the malicious process, script, or configuration responsible for the TTP.</p>
                            <p><strong>4. Harden:</strong> Apply relevant security patches and configuration changes to prevent recurrence.</p>
                        </div>
                    </div>
                </div>
                <DialogClose className="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-accent data-[state=open]:text-muted-foreground">
                    <X className="h-4 w-4" />
                    <span className="sr-only">Close</span>
                </DialogClose>
            </>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
