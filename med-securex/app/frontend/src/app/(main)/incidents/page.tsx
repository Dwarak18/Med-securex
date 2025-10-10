'use client';

import { useState, useEffect } from 'react';
import { IncidentsTable } from '@/components/incidents/IncidentsTable';
import type { Incident, IncidentSeverity, IncidentStatus } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { FileDown } from 'lucide-react';
import { IncidentStatusChart } from '@/components/incidents/IncidentStatusChart';
import { IncidentSeverityChart } from '@/components/incidents/IncidentSeverityChart';
import { RecentIncidentsTable } from '@/components/incidents/RecentIncidentsTable';
import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { useToast } from '@/hooks/use-toast';
import { getIncidents } from '@/app/actions';
import { Skeleton } from '@/components/ui/skeleton';

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { toast } = useToast();

  useEffect(() => {
    async function loadIncidents() {
      setIsLoading(true);
      const { data, error } = await getIncidents();
      if (error) {
        toast({
          variant: 'destructive',
          title: 'Failed to load incidents',
          description: error,
        });
        setIncidents([]);
      } else {
        setIncidents(data || []);
      }
      setIsLoading(false);
    }
    loadIncidents();
  }, [toast]);


  const statusCounts = incidents.reduce((acc, incident) => {
    acc[incident.status] = (acc[incident.status] || 0) + 1;
    return acc;
  }, {} as Record<IncidentStatus, number>);

  const severityCounts = incidents.reduce((acc, incident) => {
    acc[incident.severity] = (acc[incident.severity] || 0) + 1;
    return acc;
  }, {} as Record<IncidentSeverity, number>);

  const recentIncidents = [...incidents]
    .sort((a, b) => new Date(b.created).getTime() - new Date(a.created).getTime())
    .slice(0, 5);

  const handleDownloadReport = async () => {
    toast({ title: 'Generating Report...', description: 'Please wait while we prepare your PDF.' });
    try {
      const doc = new jsPDF({
        orientation: 'p',
        unit: 'px',
        format: 'a4',
      });
  
      const statusChartElement = document.getElementById('status-chart');
      const severityChartElement = document.getElementById('severity-chart');
      const recentIncidentsTableElement = document.getElementById('recent-incidents-table');
      
      doc.setTextColor(210, 40, 98); // foreground
      doc.text("Incidents Report", 20, 20);
      doc.line(20, 22, doc.internal.pageSize.getWidth() - 20, 22);
  
      doc.setFontSize(12);
      doc.text(`Total Incidents: ${incidents.length}`, 20, 40);
  
      let currentY = 50;
  
      if (statusChartElement) {
        const canvas = await html2canvas(statusChartElement, { backgroundColor: '#020817' }); // dark background
        const imgData = canvas.toDataURL('image/png');
        const imgProps = doc.getImageProperties(imgData);
        const pdfWidth = doc.internal.pageSize.getWidth();
        const imgWidth = pdfWidth / 2 - 30;
        const imgHeight = (imgProps.height * imgWidth) / imgProps.width;
        doc.addImage(imgData, 'PNG', 20, currentY, imgWidth, imgHeight);
      }
  
      if (severityChartElement) {
        const canvas = await html2canvas(severityChartElement, { backgroundColor: '#020817' });
        const imgData = canvas.toDataURL('image/png');
        const imgProps = doc.getImageProperties(imgData);
        const pdfWidth = doc.internal.pageSize.getWidth();
        const imgWidth = pdfWidth / 2 - 30;
        const imgHeight = (imgProps.height * imgWidth) / imgProps.width;
        doc.addImage(imgData, 'PNG', pdfWidth / 2, currentY, imgWidth, imgHeight);
      }
      
      currentY += 160;

      if(recentIncidentsTableElement) {
        const canvas = await html2canvas(recentIncidentsTableElement, { backgroundColor: '#020817' });
        const imgData = canvas.toDataURL('image/png');
        const imgProps = doc.getImageProperties(imgData);
        const pdfWidth = doc.internal.pageSize.getWidth();
        const imgWidth = pdfWidth - 40;
        const imgHeight = (imgProps.height * imgWidth) / imgProps.width;
        doc.addImage(imgData, 'PNG', 20, currentY, imgWidth, imgHeight);
      }
  
      doc.save("incidents-report.pdf");
      toast({ title: 'Success!', description: 'Your report has been downloaded.' });
    } catch (error) {
      console.error("Failed to generate PDF:", error);
      toast({ variant: 'destructive', title: 'Error', description: 'Failed to generate PDF report.' });
    }
  };
  
  if (isLoading) {
    return (
        <div className="flex-1 space-y-6">
            <Skeleton className="h-10 w-1/3 mx-auto" />
            <Skeleton className="h-6 w-1/2 mx-auto" />
            <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
                <Skeleton className="h-48" />
                <Skeleton className="h-48" />
                <Skeleton className="h-48" />
            </div>
            <Skeleton className="h-64" />
            <Skeleton className="h-96" />
        </div>
    );
  }

  return (
    <div className="flex-1">
      <div className="flex flex-col md:flex-row justify-between items-center mb-6 gap-4">
        <div className="text-center flex-1">
            <h1 className="text-3xl font-bold font-headline">Incidents</h1>
            <p className="text-muted-foreground">
                Track, manage, and analyze security incidents.
            </p>
        </div>
        <Button 
            onClick={handleDownloadReport}
            className="bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-2xl shadow-lg hover:scale-105 hover:brightness-90 transform transition-transform duration-200"
        >
            <FileDown className="mr-2 h-4 w-4" /> Download Report
        </Button>
      </div>
      
      {/* Report Summary Section */}
      <div className="space-y-6">
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <Card className="lg:col-span-1 flex flex-col items-center justify-center">
            <CardHeader>
              <CardTitle className="text-muted-foreground">Total Incidents</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-5xl font-bold">{incidents.length}</p>
            </CardContent>
          </Card>
          <div id="status-chart" className="lg:col-span-1">
            <IncidentStatusChart data={statusCounts} />
          </div>
          <div id="severity-chart" className="lg:col-span-1">
             <IncidentSeverityChart data={severityCounts} />
          </div>
        </div>

        <div id="recent-incidents-table">
          <RecentIncidentsTable incidents={recentIncidents} />
        </div>
      </div>

      <div className="mt-6">
        <IncidentsTable incidents={incidents} />
      </div>
    </div>
  );
}
