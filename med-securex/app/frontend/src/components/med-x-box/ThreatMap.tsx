'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function ThreatMap() {
  return (
    <Card className="rounded-2xl shadow-lg h-full">
      <CardHeader>
        <CardTitle>Threat Sources by Location</CardTitle>
        <CardDescription>Geographic distribution of incoming threats.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex items-center justify-center h-full text-muted-foreground aspect-video">
          Threat map data will be displayed here.
        </div>
      </CardContent>
    </Card>
  );
}
