import { useEffect, useState } from 'react';
import { incidentService } from '../services/incidentService';
import type { Incident } from '../types';
import { 
  AlertCircle, Clock, CheckCircle2, XCircle, Search, 
  Zap, ArrowUpRight 
} from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { cn, formatRelativeTime } from '../utils';

const Dashboard = () => {
  const navigate = useNavigate();
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedFilter, setSelectedFilter] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState('');

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
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="relative flex items-center justify-center">
          <div className="h-10 w-10 animate-spin rounded-full border-2 border-emerald-500/20 border-t-emerald-400"></div>
          <div className="absolute h-4 w-4 rounded-full bg-emerald-500/30 animate-ping"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-rose-400 font-mono text-sm">
        {error}
      </div>
    );
  }

  const openIncidents = incidents.filter(i => i.status === 'OPEN').length;
  const investigatingIncidents = incidents.filter(i => i.status === 'INVESTIGATING').length;
  const resolvedIncidents = incidents.filter(i => i.status === 'RESOLVED').length;
  const criticalIncidents = incidents.filter(i => i.severity === 'CRITICAL').length;

  const stats = [
    { id: 'ALL', name: 'Total Incidents', value: incidents.length, icon: AlertCircle, color: 'text-cyan-400', bg: 'bg-cyan-500/10', border: 'border-cyan-500/25', ring: 'ring-cyan-500/30' },
    { id: 'OPEN', name: 'Open', value: openIncidents, icon: AlertCircle, color: 'text-rose-400', bg: 'bg-rose-500/10', border: 'border-rose-500/25', ring: 'ring-rose-500/30' },
    { id: 'INVESTIGATING', name: 'Investigating', value: investigatingIncidents, icon: Clock, color: 'text-amber-400', bg: 'bg-amber-500/10', border: 'border-amber-500/25', ring: 'ring-amber-500/30' },
    { id: 'RESOLVED', name: 'Resolved', value: resolvedIncidents, icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/10', border: 'border-emerald-500/25', ring: 'ring-emerald-500/30' },
    { id: 'CRITICAL', name: 'Critical', value: criticalIncidents, icon: XCircle, color: 'text-rose-500', bg: 'bg-rose-500/15', border: 'border-rose-500/30', ring: 'ring-rose-500/40' },
  ];

  // Filtered incidents based on search & filter card
  const filteredIncidents = incidents.filter(incident => {
    // Stat card filter
    if (selectedFilter === 'OPEN' && incident.status !== 'OPEN') return false;
    if (selectedFilter === 'INVESTIGATING' && incident.status !== 'INVESTIGATING') return false;
    if (selectedFilter === 'RESOLVED' && incident.status !== 'RESOLVED') return false;
    if (selectedFilter === 'CRITICAL' && incident.severity !== 'CRITICAL') return false;

    // Text search filter
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchTitle = incident.title.toLowerCase().includes(q);
      const matchDesc = incident.description?.toLowerCase().includes(q);
      const matchSource = incident.source?.toLowerCase().includes(q);
      if (!matchTitle && !matchDesc && !matchSource) return false;
    }
    return true;
  });

  return (
    <div className="space-y-8">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 shadow-matrix-glow-sm">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              SRE OBSERVABILITY ACTIVE
            </span>
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-slate-100 via-slate-200 to-emerald-400">
            Operations Command Center
          </h1>
          <p className="text-xs font-mono text-slate-400 mt-1">
            Real-time telemetry, multi-vector evidence synthesis & autonomous hypothesis verification
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link 
            to="/incidents/new" 
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 px-5 py-2.5 text-xs font-semibold font-mono text-black shadow-matrix-glow hover:from-emerald-400 hover:to-teal-400 transition-all duration-200"
          >
            <AlertCircle className="h-4 w-4" />
            Report Incident
          </Link>
        </div>
      </div>

      {/* Metric Stat Cards - Interactive click to filter */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        {stats.map((stat) => {
          const isSelected = selectedFilter === stat.id;
          return (
            <button
              key={stat.id}
              onClick={() => setSelectedFilter(isSelected ? 'ALL' : stat.id)}
              className={cn(
                "relative rounded-xl border p-5 shadow-sm backdrop-blur transition-all duration-200 text-left group",
                isSelected 
                  ? cn("bg-matrix-surface border-emerald-400/50 shadow-matrix-glow ring-1", stat.ring)
                  : "bg-matrix-card/80 border-matrix-border hover:border-emerald-500/30 hover:bg-matrix-card"
              )}
            >
              <div className="flex items-center gap-4">
                <div className={cn("p-2.5 rounded-lg border transition-transform group-hover:scale-105", stat.bg, stat.color, stat.border)}>
                  <stat.icon className="h-5 w-5" />
                </div>
                <div>
                  <div className="flex items-center gap-1.5">
                    <p className="text-[11px] font-mono uppercase tracking-wider text-slate-400">{stat.name}</p>
                    {isSelected && <span className="text-[9px] font-mono text-emerald-400">● Active</span>}
                  </div>
                  <p className="text-2xl font-bold font-mono text-slate-100 mt-0.5">{stat.value}</p>
                </div>
              </div>
              <div className="absolute top-0 left-4 right-4 h-[1px] bg-gradient-to-r from-transparent via-emerald-500/10 to-transparent group-hover:via-emerald-500/30 transition-all"></div>
            </button>
          );
        })}
      </div>

      {/* Incident Feed with Search, Filter Chips & Quick Actions */}
      <div className="rounded-2xl border border-matrix-border bg-matrix-card/90 shadow-sm overflow-hidden backdrop-blur">
        {/* Table Controls Bar */}
        <div className="border-b border-matrix-border px-6 py-4 flex flex-col md:flex-row md:items-center justify-between gap-3 bg-matrix-surface/40">
          <div className="flex items-center gap-3">
            <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
            <h2 className="text-sm font-semibold text-slate-100 font-mono uppercase tracking-wider">
              Incident Feed ({filteredIncidents.length})
            </h2>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-2.5 h-3.5 w-3.5 text-slate-500" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Filter incidents..."
                className="pl-8 pr-3 py-1.5 bg-matrix-bg border border-matrix-border rounded-lg text-xs font-mono text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40 w-48 sm:w-60 transition-all"
              />
            </div>

            {/* Filter Pills */}
            <div className="flex items-center gap-1 bg-matrix-bg p-1 rounded-lg border border-matrix-border text-xs font-mono">
              {['ALL', 'OPEN', 'INVESTIGATING', 'RESOLVED'].map((f) => (
                <button
                  key={f}
                  onClick={() => setSelectedFilter(f)}
                  className={cn(
                    "px-2.5 py-1 rounded text-[10px] font-medium transition-colors",
                    selectedFilter === f
                      ? "bg-emerald-500/20 text-emerald-300 font-semibold border border-emerald-500/30"
                      : "text-slate-400 hover:text-slate-200"
                  )}
                >
                  {f}
                </button>
              ))}
            </div>
          </div>
        </div>

        {filteredIncidents.length === 0 ? (
          <div className="p-16 text-center text-slate-500 font-mono text-xs">
            {searchQuery || selectedFilter !== 'ALL' 
              ? 'No incidents match your search filters.' 
              : 'No incidents reported yet. Click "Report Incident" above to create one.'}
          </div>
        ) : (
          <div className="divide-y divide-matrix-border">
            {filteredIncidents.map((incident) => (
              <div 
                key={incident.id} 
                className="block hover:bg-matrix-surface/50 transition-colors p-5 group"
              >
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                  {/* Left Column: Title, tags, description */}
                  <div className="space-y-1.5 flex-1 min-w-0">
                    <div className="flex flex-wrap items-center gap-2.5">
                      <Link 
                        to={`/incidents/${incident.id}`}
                        className="font-bold text-sm text-slate-100 group-hover:text-emerald-300 transition-colors hover:underline"
                      >
                        {incident.title}
                      </Link>
                      
                      <span className={cn(
                        "px-2 py-0.5 rounded text-[10px] font-mono font-medium uppercase border",
                        incident.severity === 'CRITICAL' ? 'bg-rose-500/15 text-rose-400 border-rose-500/30' :
                        incident.severity === 'HIGH' ? 'bg-amber-500/15 text-amber-400 border-amber-500/30' :
                        'bg-slate-500/15 text-slate-400 border-slate-500/30'
                      )}>
                        {incident.severity}
                      </span>

                      <span className={cn(
                        "inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-mono font-medium border",
                        incident.status === 'RESOLVED' ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' :
                        incident.status === 'INVESTIGATING' ? 'bg-amber-500/15 text-amber-400 border-amber-500/30' :
                        'bg-rose-500/15 text-rose-400 border-rose-500/30'
                      )}>
                        {incident.status}
                      </span>
                      
                      {incident.source && (
                        <span className="text-[10px] font-mono text-slate-500 bg-matrix-surface px-2 py-0.5 rounded border border-matrix-border">
                          src: {incident.source}
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-slate-400 line-clamp-1 font-sans">
                      {incident.description || 'No description provided.'}
                    </p>

                    <div className="flex items-center gap-3 text-[11px] font-mono text-slate-500 pt-1">
                      <span title={new Date(incident.created_at).toLocaleString()}>
                        Created {formatRelativeTime(incident.created_at)}
                      </span>
                      <span>•</span>
                      <span className="truncate">ID: {incident.id.substring(0, 12)}...</span>
                    </div>
                  </div>

                  {/* Right Column: Quick Action */}
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <button
                      onClick={() => navigate(`/incidents/${incident.id}`)}
                      className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg text-xs font-mono font-semibold bg-emerald-500/10 text-emerald-300 border border-emerald-500/30 hover:bg-emerald-500/20 hover:border-emerald-500/50 shadow-matrix-glow-sm transition-all"
                    >
                      <Zap className="h-3.5 w-3.5 text-emerald-400" />
                      <span>Launch Agent</span>
                      <ArrowUpRight className="h-3 w-3 opacity-70" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;

