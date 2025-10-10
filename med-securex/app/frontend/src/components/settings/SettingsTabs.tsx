'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import type { Role } from '@/types';
import { useAuth } from '../auth/useAuth';
import { useRouter } from 'next/navigation';
import { useEffect } from 'react';

const mockUsers = [
  { id: 'usr_1', name: 'Dr. Alex Chen', email: 'alex.chen@medisecure.dev', role: 'Admin', avatarUrl: `https://i.pravatar.cc/150?u=alexchen` },
  { id: 'usr_2', name: 'Ben Carter', email: 'ben.carter@medisecure.dev', role: 'Analyst', avatarUrl: `https://i.pravatar.cc/150?u=bencarter` },
  { id: 'usr_3', name: 'Casey Day', email: 'casey.day@medisecure.dev', role: 'Analyst', avatarUrl: `https://i.pravatar.cc/150?u=caseyday` },
  { id: 'usr_4', name: 'Dana Evans', email: 'dana.evans@medisecure.dev', role: 'Viewer', avatarUrl: `https://i.pravatar.cc/150?u=danaevans` },
];


export function SettingsTabs() {
    const { role } = useAuth();
    const router = useRouter();

    useEffect(() => {
        if (role !== 'Admin') {
            router.push('/dashboard');
        }
    }, [role, router]);

    if (role !== 'Admin') {
        return <p>You do not have permission to view this page.</p>;
    }

  return (
    <Tabs defaultValue="users" className="space-y-4">
      <TabsList>
        <TabsTrigger value="users">User Management</TabsTrigger>
        <TabsTrigger value="thresholds">Alert Thresholds</TabsTrigger>
        <TabsTrigger value="retention">Log Retention</TabsTrigger>
      </TabsList>

      <TabsContent value="users" className="space-y-4">
        <Card className="rounded-2xl shadow-lg">
          <CardHeader>
            <CardTitle>User Management</CardTitle>
            <CardDescription>Manage user roles and access permissions.</CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="text-center">User</TableHead>
                  <TableHead className="text-center">Role</TableHead>
                  <TableHead className="text-center">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {mockUsers.map(user => (
                  <TableRow key={user.id}>
                    <TableCell className="text-center">
                      <div className="flex items-center gap-3 justify-center">
                        <Avatar>
                          <AvatarImage src={user.avatarUrl} data-ai-hint="user avatar" />
                          <AvatarFallback>{user.name.slice(0, 2)}</AvatarFallback>
                        </Avatar>
                        <div>
                          <p className="font-medium">{user.name}</p>
                          <p className="text-sm text-muted-foreground">{user.email}</p>
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      <Select defaultValue={user.role}>
                        <SelectTrigger className="w-[120px] mx-auto">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="Admin">Admin</SelectItem>
                          <SelectItem value="Analyst">Analyst</SelectItem>
                          <SelectItem value="Viewer">Viewer</SelectItem>
                        </SelectContent>
                      </Select>
                    </TableCell>
                    <TableCell className="text-center">
                      <Button variant="outline" size="sm">Save</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="thresholds" className="space-y-4">
        <Card className="rounded-2xl shadow-lg">
          <CardHeader>
            <CardTitle>Alert Thresholds</CardTitle>
            <CardDescription>Configure when to trigger high-severity alerts.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between space-x-4 p-4 border rounded-lg">
              <div className="space-y-1">
                <Label htmlFor="failed-logins" className="font-semibold">Failed Login Attempts</Label>
                <p className="text-sm text-muted-foreground">Trigger a high-severity alert after this many failed logins in 5 minutes.</p>
              </div>
              <Input id="failed-logins" type="number" defaultValue="5" className="w-24" />
            </div>
            <div className="flex items-center justify-between space-x-4 p-4 border rounded-lg">
              <div className="space-y-1">
                <Label htmlFor="data-exfil" className="font-semibold">Data Exfiltration</Label>
                <p className="text-sm text-muted-foreground">Trigger a critical alert if outbound data exceeds this limit in 1 minute.</p>
              </div>
              <div className="flex items-center gap-2">
                <Input id="data-exfil" type="number" defaultValue="100" className="w-24" />
                <Label>MB</Label>
              </div>
            </div>
            <div className="flex items-end justify-end">
                <Button>Save Changes</Button>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
      
      <TabsContent value="retention" className="space-y-4">
        <Card className="rounded-2xl shadow-lg">
          <CardHeader>
            <CardTitle>Log Retention Policy</CardTitle>
            <CardDescription>Set how long to retain different types of log data.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="flex items-center justify-between space-x-4 p-4 border rounded-lg">
              <div>
                <Label htmlFor="alert-logs" className="font-semibold">Alert Data</Label>
                <p className="text-sm text-muted-foreground">How long to store detailed alert information.</p>
              </div>
              <Select defaultValue="365">
                <SelectTrigger className="w-[180px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="90">90 days</SelectItem>
                  <SelectItem value="180">180 days</SelectItem>
                  <SelectItem value="365">1 year</SelectItem>
                  <SelectItem value="730">2 years</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center justify-between space-x-4 p-4 border rounded-lg">
                <div>
                    <Label htmlFor="audit-logs" className="font-semibold">Audit Logs</Label>
                    <p className="text-sm text-muted-foreground">How long to store system and user audit trails.</p>
                </div>
                <Select defaultValue="730">
                    <SelectTrigger className="w-[180px]">
                    <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                    <SelectItem value="365">1 year</SelectItem>
                    <SelectItem value="730">2 years</SelectItem>
                    <SelectItem value="1825">5 years</SelectItem>
                    </SelectContent>
                </Select>
            </div>
            <div className="flex items-center justify-between space-x-4 p-4 border rounded-lg">
              <div className="space-y-1">
                <Label htmlFor="auto-archive" className="font-semibold">Auto-archive old logs</Label>
                <p className="text-sm text-muted-foreground">Automatically move logs older than the retention period to cold storage.</p>
              </div>
              <Switch id="auto-archive" defaultChecked />
            </div>
             <div className="flex items-end justify-end">
                <Button>Save Policy</Button>
            </div>
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}
