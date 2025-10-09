'use server';

import { correlateAlertsTTP, type CorrelateAlertsTTPInput, type CorrelateAlertsTTPOutput } from '@/ai/flows/correlate-alerts-ttp';
import type { Alert, Incident, TTP } from '@/types';

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://127.0.0.1:8000';

async function fetchFromGateway<T>(endpoint: string, options: RequestInit = {}): Promise<{ data: T | null; error: string | null }> {
  try {
    const response = await fetch(`${GATEWAY_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      cache: 'no-store', // Always fetch fresh data
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API Gateway returned an error for ${endpoint}: ${response.status} ${errorText}`);
      return { data: null, error: `API Gateway error: ${response.status} - ${errorText}` };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (e: any) {
    console.error(`Error fetching from ${endpoint}:`, e);
     if (e.cause?.code === 'ECONNREFUSED') {
        return { data: null, error: 'Could not connect to the API Gateway. Please ensure the Python gateway service is running on port 8000.' };
    }
    return { data: null, error: `Failed to fetch from ${endpoint}. Please check the server logs.` };
  }
}

export async function getDashboardMetrics(): Promise<{ data: { alerts: number; incidents: number; systems: number; } | null; error: string | null }> {
    return fetchFromGateway('/dashboard/metrics');
}

export async function getAlerts(): Promise<{ data: Alert[] | null; error: string | null }> {
    return fetchFromGateway('/alerts');
}

export async function getIncidents(): Promise<{ data: Incident[] | null; error: string | null }> {
    return fetchFromGateway('/incidents');
}

export async function getShieldUsage(): Promise<{ data: { requests: number; blocked: number; } | null; error: string | null }> {
    return fetchFromGateway('/shield/usage');
}

export async function getMedXTraffic(): Promise<{ data: { packets: number; malicious: number; } | null; error: string | null }> {
    return fetchFromGateway('/medx/traffic');
}

export async function getTTPs(): Promise<{ data: TTP[] | null; error: string | null }> {
    return fetchFromGateway('/ttps');
}

export async function getPiiReports(): Promise<{ data: { found: number; types: string[]; } | null; error: string | null }> {
    return fetchFromGateway('/pii/reports');
}


export async function getTtpCorrelation(input: CorrelateAlertsTTPInput): Promise<{ data: CorrelateAlertsTTPOutput | null; error: string | null }> {
  try {
    const result = await correlateAlertsTTP(input);
    return { data: result, error: null };
  } catch (e: any) {
    console.error('Error in TTP correlation flow:', e);
    return { data: null, error: e.message || 'An unexpected error occurred.' };
  }
}

export async function getSuricataAlerts(limit: number = 50): Promise<{ data: any; error: string | null }> {
  const adminKey = "supersecretadminkey";
  
  try {
    const response = await fetch(`${GATEWAY_URL}/admin/suricata-alerts?key=${adminKey}&limit=${limit}`, {
      cache: 'no-store',
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error(`API Gateway returned an error: ${response.status} ${errorText}`);
      if (response.status === 500 && errorText.includes("eve.json not found")) {
        return { data: null, error: 'Could not connect to the API Gateway. Is Suricata running and configured correctly? eve.json not found.' };
      }
       if (response.status === 502) {
         return { data: null, error: 'Could not connect to the API Gateway. Is the gateway running? Upstream request failed.' };
       }
      return { data: null, error: `API Gateway error: ${response.status} - ${errorText}` };
    }

    const data = await response.json();
    return { data, error: null };
  } catch (e: any) {
    console.error('Error fetching Suricata alerts:', e);
    if (e.cause?.code === 'ECONNREFUSED') {
        return { data: null, error: 'Could not connect to the API Gateway. Please ensure the Python gateway service is running on port 8000.' };
    }
    return { data: null, error: 'Failed to fetch Suricata alerts. Please check the server logs.' };
  }
}
