import { Link, Outlet, useLocation } from 'react-router-dom';
import { ShieldAlert, LayoutDashboard, List, Activity } from 'lucide-react';
import { cn } from '../utils';

const Layout = () => {
  const location = useLocation();

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Incidents', path: '/incidents', icon: List },
  ];

  return (
    <div className="min-h-screen bg-zinc-950 flex flex-col font-sans text-zinc-300">
      <header className="sticky top-0 z-50 w-full border-b border-zinc-800 bg-zinc-950/80 backdrop-blur">
        <div className="container mx-auto flex h-14 items-center px-4">
          <div className="flex items-center gap-2 font-semibold text-zinc-100">
            <ShieldAlert className="h-5 w-5 text-indigo-500" />
            <span>AI Incident Investigation Agent</span>
          </div>
          <div className="ml-8 flex items-center space-x-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors hover:bg-zinc-800/50 hover:text-zinc-50",
                    isActive ? "bg-zinc-800 text-zinc-50" : "text-zinc-400"
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.name}
                </Link>
              );
            })}
          </div>
          <div className="ml-auto flex items-center space-x-4">
            <Activity className="h-4 w-4 text-emerald-500 animate-pulse" />
            <span className="text-xs font-medium text-emerald-500">System Healthy</span>
          </div>
        </div>
      </header>
      <main className="flex-1 container mx-auto p-6 lg:p-8">
        <Outlet />
      </main>
    </div>
  );
};

export default Layout;
