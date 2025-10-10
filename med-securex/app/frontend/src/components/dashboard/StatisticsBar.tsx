'use client';

import { useState, useEffect } from 'react';
import { db } from '@/lib/firebase';
import { collection, query, where, onSnapshot, Timestamp, getDocs } from 'firebase/firestore';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Calendar as CalendarIcon, FileDown, Rocket } from 'lucide-react';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';
import { DateRange } from 'react-day-picker';
import { addDays, format, startOfMonth } from 'date-fns';
import { Skeleton } from '@/components/ui/skeleton';
import { motion, useSpring, useTransform, animate } from 'framer-motion';
import { useToast } from '@/hooks/use-toast';
import { useRouter } from 'next/navigation';
import type { Incident } from '@/types';
import { cn } from '@/lib/utils';

interface StatData {
  totalAlerts: number;
  highSeverityAlerts: number;
  authFailures: number;
  authSuccesses: number;
}

function AnimatedNumber({ value }: { value: number }) {
    const spring = useSpring(0, { mass: 0.8, stiffness: 100, damping: 20 });
    const display = useTransform(spring, (current) => Math.round(current).toLocaleString());

    useEffect(() => {
        spring.set(value);
    }, [spring, value]);

    return <motion.span>{display}</motion.span>;
}

const StatCard = ({ title, value, color, isLoading }: { title: string; value: number | null; color: string; isLoading: boolean }) => (
  <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
    <Card className="rounded-2xl shadow-lg h-full">
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-9 w-3/4" />
        ) : (
          <div className={`text-3xl font-bold ${color}`}>
            {value !== null ? <AnimatedNumber value={value} /> : 'Error'}
          </div>
        )}
      </CardContent>
    </Card>
  </motion.div>
);

export function StatisticsBar() {
  const [stats, setStats] = useState<StatData | null>(null);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { toast } = useToast();
  const router = useRouter();

  const [date, setDate] = useState<DateRange | undefined>({
    from: startOfMonth(new Date()),
    to: new Date(),
  });
  
  const getRandomValue = (min: number, max: number) => {
    return Math.floor(Math.random() * (max - min + 1)) + min;
  }

  useEffect(() => {
    if (!date?.from || !date?.to) return;
    
    setIsLoading(true);
    setError(null);

    const timer = setTimeout(() => {
        setStats({
          totalAlerts: getRandomValue(800, 1500),
          highSeverityAlerts: getRandomValue(50, 150),
          authFailures: getRandomValue(20, 80),
          authSuccesses: getRandomValue(700, 1200),
        });
        setIsLoading(false);
    }, 300);


    return () => {
      clearTimeout(timer);
    };

  }, [date, toast]);
  
  const handleGenerateReport = async () => {
    try {
      const incidentsCollection = collection(db, 'incidents');
      const incidentsSnapshot = await getDocs(incidentsCollection);
      const incidentsData = incidentsSnapshot.docs.map(doc => ({ id: doc.id, ...doc.data() } as Incident));

      if (incidentsData.length === 0) {
        toast({ title: 'No Incidents', description: 'There are no incidents to report.' });
        return;
      }
      
      const headers = Object.keys(incidentsData[0]);
      const csvRows = [
        headers.join(','),
        ...incidentsData.map(row =>
          headers.map(fieldName =>
            JSON.stringify(row[fieldName as keyof Incident] ?? '', (key, value) => value ?? '')
          ).join(',')
        )
      ];

      const csvContent = csvRows.join('\n');
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const link = document.createElement('a');
      if (link.href) {
        URL.revokeObjectURL(link.href);
      }
      const url = URL.createObjectURL(blob);
      link.href = url;
      link.setAttribute('download', 'incident_report.csv');
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      toast({
        title: "Report Generated",
        description: "Your incident report has been downloaded.",
      });

    } catch (error: any) {
      console.error("Error generating report: ", error);
      toast({
        variant: "destructive",
        title: "Report Failed",
        description: "Could not generate the incident report. " + error.message,
      });
    }
  };
  
  const handleExploreAgent = () => {
    router.push('/agents');
  };

  const statCards = [
    { title: "Total Alerts", value: stats?.totalAlerts ?? 0, color: "text-blue-500", isLoading: isLoading },
    { title: "Level 12+ Alerts", value: stats?.highSeverityAlerts ?? 0, color: "text-red-500", isLoading: isLoading },
    { title: "Authentication Failures", value: stats?.authFailures ?? 0, color: "text-red-500", isLoading: isLoading },
    { title: "Authentication Success", value: stats?.authSuccesses ?? 0, color: "text-blue-500", isLoading: isLoading },
  ]

  return (
    <div className="space-y-4">
      <div className="flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="flex-1">
            {/* Placeholder for potential title or description */}
        </div>
        <div className="flex flex-col sm:flex-row items-center gap-2">
            <Popover>
            <PopoverTrigger asChild>
                <Button
                variant={'outline'}
                className={cn(
                    "w-full sm:w-[280px] justify-start text-left font-normal rounded-full border-border"
                )}
                >
                <CalendarIcon className="mr-2 h-4 w-4" />
                {date?.from ? (
                    date.to ? (
                    <>
                        {format(date.from, 'LLL dd, y')} - {format(date.to, 'LLL dd, y')}
                    </>
                    ) : (
                    format(date.from, 'LLL dd, y')
                    )
                ) : (
                    <span>Pick a date</span>
                )}
                </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0" align="end">
                <Calendar
                initialFocus
                mode="range"
                defaultMonth={date?.from}
                selected={date}
                onSelect={setDate}
                numberOfMonths={2}
                />
            </PopoverContent>
            </Popover>
           <Button variant="outline" onClick={handleExploreAgent} className={cn("w-full sm:w-auto rounded-full border-border")}><Rocket className="mr-2 h-4 w-4"/> Explore Agent</Button>
           <Button 
                onClick={handleGenerateReport} 
                className={cn("w-full sm:w-auto rounded-full")}
            >
                <FileDown className="mr-2 h-4 w-4"/> Generate Report
            </Button>
        </div>
      </div>
      
      {error && <div className="text-red-500 p-4 bg-red-50 rounded-lg">{error}</div>}

      <div className="grid gap-4 grid-cols-1 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map(card => <StatCard key={card.title} {...card} />)}
      </div>
    </div>
  );
}
