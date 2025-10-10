'use client';

import { Badge } from '@/components/ui/badge';
import type { AlertStatus, IncidentStatus } from '@/types';
import { cn } from '@/lib/utils';

type Status = AlertStatus | IncidentStatus;

interface StatusBadgeProps {
  status: Status;
}

const statusStyles: Record<Status, string> = {
  // Alert Statuses
  'New': 'bg-red-600 text-white border-transparent hover:bg-red-600/80',
  'In Progress': 'bg-orange-500 text-white border-transparent hover:bg-orange-500/80',
  'Resolved': 'bg-green-600 text-white border-transparent hover:bg-green-600/80',
  'Dismissed': 'bg-gray-500 text-white border-transparent hover:bg-gray-500/80',
  // Incident Statuses (re-using some from alerts)
  'Open': 'bg-red-600 text-white border-transparent hover:bg-red-600/80',
  'Closed': 'bg-blue-600 text-white border-transparent hover:bg-blue-600/80',
};

export function StatusBadge({ status }: StatusBadgeProps) {
  return (
    <Badge className={cn(statusStyles[status] || 'bg-gray-500 text-white', 'whitespace-nowrap')}>
      {status}
    </Badge>
  );
}
