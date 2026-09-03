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
    <div className="min-h-screen bg-matrix-bg flex flex-col font-sans text-slate-300">
      <header className="sticky top-0 z-50 w-full border-b border-matrix-border bg-matrix-bg/85 backdrop-blur-md">
        <div className="container mx-auto flex h-16 items-center px-4">
          <Link to="/" className="flex items-center gap-3 group">
            <div className="relative flex items-center justify-center p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 shadow-matrix-glow-sm group-hover:border-emerald-500/60 transition-all duration-300">
              <ShieldAlert className="h-5 w-5 text-emerald-400 group-hover:text-emerald-300 transition-colors" />
              <div className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-emerald-400 animate-ping"></div>
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-base tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-slate-100 via-slate-200 to-emerald-400">
                AI Incident Investigator
              </span>
              <span className="text-[10px] uppercase font-mono tracking-widest text-emerald-400/80 -mt-0.5">
                Stealth SRE Agent
              </span>
            </div>
          </Link>
          <div className="ml-10 flex items-center space-x-2">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.path || (item.path !== '/' && location.pathname.startsWith(item.path));
              return (
                <Link
                  key={item.path}
                  to={item.path}
                  className={cn(
                    "flex items-center gap-2 px-3.5 py-1.5 rounded-lg text-sm font-medium transition-all duration-200",
                    isActive
                      ? "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30 shadow-matrix-glow-sm font-semibold"
                      : "text-slate-400 hover:text-slate-200 hover:bg-matrix-surface hover:border hover:border-matrix-border border border-transparent"
                  )}
                >
                  <Icon className={cn("h-4 w-4", isActive ? "text-emerald-400" : "text-slate-400")} />
                  {item.name}
                </Link>
              );
            })}
          </div>
          <div className="ml-auto flex items-center">
            <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-950/30 border border-emerald-500/30 shadow-matrix-glow-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <Activity className="h-3.5 w-3.5 text-emerald-400" />
              <span className="text-xs font-mono font-medium text-emerald-400 tracking-wide">SYSTEM LIVE</span>
            </div>
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
