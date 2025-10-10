'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

const blockedData = [
    { rank: 1, source: '198.51.100.22', category: 'Malware', count: 1452 },
    { rank: 2, source: 'evil-domain.com', category: 'Phishing', count: 987 },
    { rank: 3, source: '203.0.113.89', category: 'C2', count: 765 },
    { rank: 4, source: 'another-bad.net', category: 'Malware', count: 543 },
    { rank: 5, source: '192.0.2.14', category: 'Scanning', count: 321 },
];

export function TopBlockedTable() {
  return (
    <Card className="rounded-2xl shadow-lg h-full">
      <CardHeader>
        <CardTitle>Top Blocked Sources</CardTitle>
        <CardDescription>Most frequently blocked domains and IPs.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-center">Rank</TableHead>
              <TableHead className="text-center">Source</TableHead>
              <TableHead className="text-center">Category</TableHead>
              <TableHead className="text-center">Count</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {blockedData.map((item) => (
              <TableRow key={item.rank}>
                <TableCell className="font-medium text-center">{item.rank}</TableCell>
                <TableCell className="font-mono text-center">{item.source}</TableCell>
                <TableCell className="text-center"><Badge variant="secondary">{item.category}</Badge></TableCell>
                <TableCell className="text-center">{item.count.toLocaleString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
