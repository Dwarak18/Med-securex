import { SettingsTabs } from '@/components/settings/SettingsTabs';

export default function SettingsPage() {
  return (
    <div className="flex-1">
      <h1 className="text-3xl font-bold font-headline text-center mb-4">Settings</h1>
      <p className="text-muted-foreground text-center">
        Manage your organization's security settings. Available to Admins only.
      </p>
      <div className="pt-2">
        <SettingsTabs />
      </div>
    </div>
  );
}
