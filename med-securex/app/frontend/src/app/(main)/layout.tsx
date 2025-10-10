'use client';

import { useEffect, type ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/components/auth/useAuth';
import { Button } from '@/components/ui/button';
import {
  SidebarProvider,
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarMenu,
  SidebarMenuItem,
  SidebarTrigger,
  SidebarHeader,
  useSidebar,
  SidebarInset,
} from '@/components/ui/sidebar';
import {
  Bell,
  LayoutDashboard,
  LogOut,
  Settings,
  ShieldAlert,
  HeartPulse,
  Archive,
  ClipboardList,
  FileText,
  BarChart,
  Rocket,
  UserCircle,
  Network
} from 'lucide-react';
import Link from 'next/link';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { auth } from '@/lib/firebase';
import { ModeToggle } from '@/components/ui/mode-toggle';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';
import Image from 'next/image';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';

function NavItem({ item, pathname }: { item: NavItemType; pathname: string }) {
  const { isCollapsed } = useSidebar();
  const isActive = pathname.startsWith(item.href);

  const linkContent = (
    <>
      <item.icon className="h-4 w-4 shrink-0" />
      <span
        className={cn(
          'overflow-hidden text-ellipsis whitespace-nowrap',
          isCollapsed && 'hidden'
        )}
      >
        {item.label}
      </span>
    </>
  );
  
  const linkClasses = cn(
    "flex items-center gap-3 rounded-md px-3 py-2 text-muted-foreground transition-colors duration-200",
    "hover:bg-accent hover:text-accent-foreground",
    "focus-visible:bg-accent focus-visible:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
    isActive && "bg-accent text-accent-foreground",
    isCollapsed && "justify-center"
  );

  return (
    <SidebarMenuItem>
      {isCollapsed ? (
        <Tooltip>
          <TooltipTrigger asChild>
            <Link href={item.href} className={linkClasses}>
              {linkContent}
            </Link>
          </TooltipTrigger>
          <TooltipContent side="right" sideOffset={5}>
            {item.label}
          </TooltipContent>
        </Tooltip>
      ) : (
        <Link href={item.href} className={linkClasses}>
          {linkContent}
        </Link>
      )}
    </SidebarMenuItem>
  );
}

type NavItemType = {
  href: string;
  label: string;
  icon: React.ElementType;
  roles: string[];
};

const navItems: NavItemType[] = [
  { href: '/overview', label: 'Overview', icon: LayoutDashboard, roles: ['Admin', 'Analyst', 'Viewer'] },
  { href: '/health-api-shield', label: 'Health API Shield', icon: HeartPulse, roles: ['Admin', 'Analyst', 'Viewer'] },
  { href: '/med-x-box', label: 'MED x Box', icon: Archive, roles: ['Admin', 'Analyst', 'Viewer'] },
  { href: '/api-gateway', label: 'API Gateway', icon: Network, roles: ['Admin', 'Analyst'] },
  { href: '/alerts', label: 'Alerts', icon: ShieldAlert, roles: ['Admin', 'Analyst', 'Viewer'] },
  { href: '/incidents', label: 'Incidents', icon: FileText, roles: ['Admin', 'Analyst'] },
  { href: '/ttps', label: 'TTPs', icon: BarChart, roles: ['Admin', 'Analyst'] },
  { href: '/pii-reports', label: 'PII Reports', icon: ClipboardList, roles: ['Admin', 'Analyst'] },
  { href: '/agents', label: 'Agents', icon: Rocket, roles: ['Admin', 'Analyst', 'Viewer'] },
  { href: '/settings', label: 'Settings', icon: Settings, roles: ['Admin'] },
];

function AppLayout({ user, children }: { user: any; children: ReactNode }) {
  const { role, setUser, setRole } = useAuth();
  const { isCollapsed } = useSidebar();
  const router = useRouter();
  const pathname = usePathname();

  const filteredNavItems = navItems.filter(
    (item) => role && item.roles.includes(role)
  );

  const getPageData = (path: string) => {
    return navItems.find((item) => path.startsWith(item.href));
  };
  const currentPage = getPageData(pathname);

  const handleLogout = async () => {
    await auth.signOut();
    setUser(null);
    setRole(null);
    localStorage.removeItem('medi-secure-x2-user');
    router.push('/login');
  };

  return (
    <div className="flex min-h-screen">
      <Sidebar>
        <SidebarHeader>
           <Link href="/overview" className={cn("flex items-center gap-2 h-14", isCollapsed ? "justify-center px-0" : "px-3")}>
             <Image src="/logo.png" alt="MedSecureX Logo" width={32} height={32} className="h-8 w-8 text-primary shrink-0" />
              <div className={cn("overflow-hidden transition-all duration-300", isCollapsed ? "w-0" : "w-auto")}>
                <span className="font-bold bg-gradient-to-r from-teal-400 via-blue-600 to-teal-400 bg-clip-text text-transparent whitespace-nowrap text-xl">
                    MedSecureX
                </span>
              </div>
          </Link>
        </SidebarHeader>

        <SidebarContent>
          <ScrollArea className="flex-1">
            <SidebarMenu>
              {filteredNavItems.map((item) => (
                <NavItem key={item.href} item={item} pathname={pathname} />
              ))}
            </SidebarMenu>
          </ScrollArea>
        </SidebarContent>

        <SidebarFooter>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="w-full justify-start p-2 interactive-glow">
                <UserCircle className="h-6 w-6 shrink-0" />
                <div
                  className={cn(
                    'flex-1 overflow-hidden text-ellipsis whitespace-nowrap text-left ml-2',
                    isCollapsed && 'hidden'
                  )}
                >
                  <p className="text-sm font-medium leading-none">
                    {user.name}
                  </p>
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              className="w-56 mb-2 ml-2"
              align="end"
              forceMount
            >
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none">
                    {user.name}
                  </p>
                  <p className="text-xs leading-none text-muted-foreground">
                    {user.email}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleLogout}>
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </SidebarFooter>
      </Sidebar>

      <SidebarInset>
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between gap-4 border-b bg-background px-4">
          <div className="flex items-center gap-2">
            <SidebarTrigger />
            {currentPage && (
              <h1 className="text-lg font-semibold md:text-xl font-headline text-muted-foreground">
                {currentPage.label}
              </h1>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="icon"
              className="h-9 w-9"
              onClick={handleLogout}
            >
              <LogOut className="h-4 w-4" />
              <span className="sr-only">Sign Out</span>
            </Button>
            <Button variant="ghost" size="icon" className="h-9 w-9">
              <Bell className="h-4 w-4" />
              <span className="sr-only">Toggle notifications</span>
            </Button>
            <ModeToggle />
          </div>
        </header>
        <main className="flex-1 p-6">{children}</main>
      </SidebarInset>
    </div>
  );
}

export default function MainLayout({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  if (loading || !user) {
    return (
      <div className="flex h-screen items-center justify-center">
        Loading...
      </div>
    );
  }

  return (
    <SidebarProvider>
      <AppLayout user={user}>{children}</AppLayout>
    </SidebarProvider>
  );
}
