import { useEffect, useState } from 'react';
import { incidentService } from '../services/incidentService';
import type { Incident } from '../types';
import { AlertCircle, Clock, CheckCircle2, XCircle } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '../utils';

const Dashboard = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDashboard = async () => {
      try {
        setLoading(true);
        const data = await incidentService.getIncidents(0, 100);
        setIncidents(data);
      } catch (err: any) {
        console.error("Dashboard failed to load data:", err);
        setError(`Failed to load dashboard data: ${err.message || 'Unknown error'}`);
      } finally {
        setLoading(false);
      }
    };
    loadDashboard();
  }, []);

  if (loading) {
    return <div className="flex h-64 items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div></div>;
  }

  if (error) {
    return <div className="rounded-md bg-red-500/10 p-4 text-red-500">{error}</div>;
  }

  const openIncidents = incidents.filter(i => i.status === 'OPEN').length;
  const investigatingIncidents = incidents.filter(i => i.status === 'INVESTIGATING').length;
  const resolvedIncidents = incidents.filter(i => i.status === 'RESOLVED').length;
  const criticalIncidents = incidents.filter(i => i.severity === 'CRITICAL').length;

  const stats = [
    { name: 'Total Incidents', value: incidents.length, icon: AlertCircle, color: 'text-blue-500', bg: 'bg-blue-500/10' },
    { name: 'Open', value: openIncidents, icon: AlertCircle, color: 'text-rose-500', bg: 'bg-rose-500/10' },
    { name: 'Investigating', value: investigatingIncidents, icon: Clock, color: 'text-amber-500', bg: 'bg-amber-500/10' },
    { name: 'Resolved', value: resolvedIncidents, icon: CheckCircle2, color: 'text-emerald-500', bg: 'bg-emerald-500/10' },
    { name: 'Critical', value: criticalIncidents, icon: XCircle, color: 'text-red-500', bg: 'bg-red-500/10' },
  ];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <Link to="/incidents/new" className="inline-flex items-center justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow transition-colors hover:bg-indigo-700 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-indigo-500">
          Report Incident
        </Link>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        {stats.map((stat) => (
          <div key={stat.name} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 shadow-sm backdrop-blur">
            <div className="flex items-center gap-4">
              <div className={cn("p-3 rounded-lg", stat.bg, stat.color)}>
                <stat.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-sm font-medium text-zinc-400">{stat.name}</p>
                <p className="text-2xl font-bold">{stat.value}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="mt-8 rounded-xl border border-zinc-800 bg-zinc-900/50 shadow-sm overflow-hidden">
        <div className="border-b border-zinc-800 px-6 py-4">
          <h2 className="text-lg font-medium">Recent Incidents</h2>
        </div>
        {incidents.length === 0 ? (
          <div className="p-8 text-center text-zinc-500">
            No incidents reported yet.
          </div>
        ) : (
          <div className="divide-y divide-zinc-800">
            {incidents.slice(0, 5).map((incident) => (
              <Link key={incident.id} to={`/incidents/${incident.id}`} className="block hover:bg-zinc-800/50 transition-colors">
                <div className="px-6 py-4">
                  <div className="flex items-center justify-between">
                    <p className="font-medium text-zinc-200">{incident.title}</p>
                    <div className="flex items-center gap-2">
                      <span className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                        incident.status === 'RESOLVED' ? 'bg-emerald-500/10 text-emerald-500' :
                        incident.status === 'INVESTIGATING' ? 'bg-amber-500/10 text-amber-500' :
                        'bg-rose-500/10 text-rose-500'
                      )}>
                        {incident.status}
                      </span>
                    </div>
                  </div>
                  <div className="mt-1 flex text-xs text-zinc-500">
                    <span>{new Date(incident.created_at).toLocaleString()}</span>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
