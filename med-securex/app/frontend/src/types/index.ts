export type Role = 'Admin' | 'Analyst' | 'Viewer';

export interface User {
  uid: string;
  name: string;
  email: string;
  avatarUrl: string;
  role: Role;
}

export type AlertSeverity = 'Critical' | 'High' | 'Medium' | 'Low';
export type AlertStatus = 'New' | 'In Progress' | 'Resolved' | 'Dismissed';

export interface Alert {
  id: string;
  timestamp: string;
  severity: AlertSeverity;
  description: string;
  ttp_id: string;
  status: AlertStatus;
  source: string;
  entity: string;
}

export type IncidentStatus = 'Open' | 'In Progress' | 'Resolved' | 'Closed';
export type IncidentSeverity = 'Critical' | 'High' | 'Medium' | 'Low';

export interface Incident {
  id: string;
  title: string;
  status: IncidentStatus;
  severity: IncidentSeverity;
  assignee: string;
  created: string;
}

export interface TTP {
  id: string;
  name: string;
  tactic: string;
  description: string;
  source: string; // Corresponds to Signature
  endpoint: string; // Corresponds to Payload
  count: number;
  lastSeen: string;
}
