'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';

const piiData = [
  { type: 'Date of Birth (DOB)', count: 4521, trend: 12.5 },
  { type: 'Social Security Number (SSN)', count: 3890, trend: 8.2 },
  { type: 'Home Address', count: 2105, trend: -2.1 },
  { type: 'Medical Record Number (MRN)', count: 1854, trend: 5.6 },
  { type: 'Phone Number', count: 1532, trend: 1.5 },
];

export function TopPiiTypesTable() {
  const total = piiData.reduce((acc, item) => acc + item.count, 0);

  return (
    <Card className="rounded-2xl shadow-lg h-full">
      <CardHeader>
        <CardTitle>Top Scrubbed PII Types</CardTitle>
        <CardDescription>Most frequently identified and scrubbed PII fields.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead className="text-center">PII Type</TableHead>
              <TableHead className="text-center">Count (30d)</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {piiData.map((item) => (
              <TableRow key={item.type}>
                <TableCell className="font-medium text-center">
                  <div className="flex flex-col gap-1">
                    <span>{item.type}</span>
                     <Progress value={(item.count / total) * 100} className="h-2" />
                  </div>
                </TableCell>
                <TableCell className="text-center font-mono">{item.count.toLocaleString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
