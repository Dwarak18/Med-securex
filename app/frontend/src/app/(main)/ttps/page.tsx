'use client';

import { useState, useEffect } from 'react';
import { TTPsTable } from '@/components/ttps/TTPsTable';
import { TTPsBubbleChart } from '@/components/ttps/TTPsBubbleChart';
import type { TTP } from '@/types';
import { getTTPs } from '@/app/actions';
import { useToast } from '@/hooks/use-toast';
import { Skeleton } from '@/components/ui/skeleton';

export default function TTPsPage() {
  const [ttps, setTtps] = useState<TTP[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedTactic, setSelectedTactic] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    async function loadTTPs() {
      setIsLoading(true);
      const { data, error } = await getTTPs();
      if (error) {
        toast({
          variant: 'destructive',
          title: 'Failed to load TTPs',
          description: error,
        });
        setTtps([]);
      } else {
        setTtps(data || []);
      }
      setIsLoading(false);
    }
    loadTTPs();
  }, [toast]);
  
  if (isLoading) {
    return (
        <div className="flex-1 space-y-6">
            <Skeleton className="h-[500px] w-full" />
            <Skeleton className="h-96 w-full" />
        </div>
    )
  }

  return (
    <div className="flex-1 space-y-6">
      <TTPsBubbleChart ttps={ttps} onBubbleClick={setSelectedTactic} />
      <TTPsTable ttps={ttps} selectedTactic={selectedTactic} />
    </div>
  );
}
