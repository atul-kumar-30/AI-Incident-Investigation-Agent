import { useEffect, useState } from 'react';
import { incidentService } from '../services/incidentService';
import type { Incident } from '../types';
import { Link } from 'react-router-dom';
import { cn } from '../utils';

const IncidentList = () => {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Basic pagination state
  const [page, setPage] = useState(0);
  const limit = 10;

  useEffect(() => {
    const loadIncidents = async () => {
      try {
        setLoading(true);
        const data = await incidentService.getIncidents(page * limit, limit);
        setIncidents(data);
        setError(null);
      } catch (err) {
        setError('Failed to load incidents.');
      } finally {
        setLoading(false);
      }
    };

    loadIncidents();
  }, [page]);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-slate-100 via-slate-200 to-emerald-400">
            Incident Log
          </h1>
          <p className="text-sm font-mono text-slate-400 mt-1">
            Recorded production anomalies, outages, and agent investigations
          </p>
        </div>
        <Link 
          to="/incidents/new" 
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 px-5 py-2.5 text-sm font-semibold text-black shadow-matrix-glow hover:from-emerald-400 hover:to-teal-400 transition-all duration-200"
        >
          Report Incident
        </Link>
      </div>

      <div className="rounded-xl border border-matrix-border bg-matrix-card/90 shadow-sm overflow-hidden backdrop-blur">
        {loading && incidents.length === 0 ? (
          <div className="flex h-64 items-center justify-center">
            <div className="relative flex items-center justify-center">
              <div className="h-10 w-10 animate-spin rounded-full border-2 border-emerald-500/20 border-t-emerald-400"></div>
              <div className="absolute h-4 w-4 rounded-full bg-emerald-500/30 animate-ping"></div>
            </div>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-rose-400 font-mono text-sm">{error}</div>
        ) : incidents.length === 0 ? (
          <div className="p-16 text-center">
            <h3 className="text-base font-semibold text-slate-200">No incidents found</h3>
            <p className="mt-1 text-sm font-mono text-slate-500">Get started by reporting a new incident.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-slate-300">
              <thead className="bg-matrix-surface/80 text-xs font-mono uppercase tracking-wider text-slate-400 border-b border-matrix-border">
                <tr>
                  <th scope="col" className="px-6 py-4 font-medium">Title</th>
                  <th scope="col" className="px-6 py-4 font-medium">Status</th>
                  <th scope="col" className="px-6 py-4 font-medium">Severity</th>
                  <th scope="col" className="px-6 py-4 font-medium">Source</th>
                  <th scope="col" className="px-6 py-4 font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-matrix-border">
                {incidents.map((incident) => (
                  <tr key={incident.id} className="hover:bg-matrix-surface/50 transition-colors group">
                    <td className="px-6 py-4">
                      <Link to={`/incidents/${incident.id}`} className="font-semibold text-slate-200 group-hover:text-emerald-400 transition-colors">
                        {incident.title}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <span className={cn(
                        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-mono font-medium border",
                        incident.status === 'RESOLVED' ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' :
                        incident.status === 'INVESTIGATING' ? 'bg-amber-500/15 text-amber-400 border-amber-500/30' :
                        'bg-rose-500/15 text-rose-400 border-rose-500/30'
                      )}>
                        {incident.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-mono font-medium border",
                        incident.severity === 'CRITICAL' ? 'bg-rose-500/15 text-rose-400 border-rose-500/30' :
                        incident.severity === 'HIGH' ? 'bg-amber-500/15 text-amber-400 border-amber-500/30' :
                        'bg-slate-500/15 text-slate-400 border-slate-500/30'
                      )}>
                        {incident.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4 font-mono text-xs text-slate-400">{incident.source}</td>
                    <td className="px-6 py-4 whitespace-nowrap font-mono text-xs text-slate-500">{new Date(incident.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {/* Pagination Controls */}
        <div className="flex items-center justify-between border-t border-matrix-border bg-matrix-surface/40 px-6 py-3">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0 || loading}
            className="rounded-lg border border-matrix-border bg-matrix-card px-3.5 py-1.5 text-xs font-mono text-slate-300 hover:bg-emerald-500/10 hover:border-emerald-500/30 disabled:opacity-40 transition-colors"
          >
            ← Previous
          </button>
          <span className="text-xs font-mono text-slate-400">Page {page + 1}</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={incidents.length < limit || loading}
            className="rounded-lg border border-matrix-border bg-matrix-card px-3.5 py-1.5 text-xs font-mono text-slate-300 hover:bg-emerald-500/10 hover:border-emerald-500/30 disabled:opacity-40 transition-colors"
          >
            Next →
          </button>
        </div>
      </div>
    </div>
  );
};

export default IncidentList;
