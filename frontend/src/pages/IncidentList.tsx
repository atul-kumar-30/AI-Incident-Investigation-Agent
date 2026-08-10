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
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold tracking-tight">Incidents</h1>
        <Link to="/incidents/new" className="inline-flex items-center justify-center rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow transition-colors hover:bg-indigo-700">
          Report Incident
        </Link>
      </div>

      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 shadow-sm overflow-hidden">
        {loading && incidents.length === 0 ? (
          <div className="flex h-64 items-center justify-center">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
          </div>
        ) : error ? (
          <div className="p-8 text-center text-red-500">{error}</div>
        ) : incidents.length === 0 ? (
          <div className="p-12 text-center">
            <h3 className="mt-2 text-sm font-semibold text-zinc-300">No incidents</h3>
            <p className="mt-1 text-sm text-zinc-500">Get started by reporting a new incident.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm text-zinc-400">
              <thead className="bg-zinc-900 text-xs uppercase text-zinc-500 border-b border-zinc-800">
                <tr>
                  <th scope="col" className="px-6 py-4 font-medium">Title</th>
                  <th scope="col" className="px-6 py-4 font-medium">Status</th>
                  <th scope="col" className="px-6 py-4 font-medium">Severity</th>
                  <th scope="col" className="px-6 py-4 font-medium">Source</th>
                  <th scope="col" className="px-6 py-4 font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-zinc-800">
                {incidents.map((incident) => (
                  <tr key={incident.id} className="hover:bg-zinc-800/50 transition-colors">
                    <td className="px-6 py-4">
                      <Link to={`/incidents/${incident.id}`} className="font-medium text-indigo-400 hover:text-indigo-300">
                        {incident.title}
                      </Link>
                    </td>
                    <td className="px-6 py-4">
                      <span className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                        incident.status === 'RESOLVED' ? 'bg-emerald-500/10 text-emerald-500' :
                        incident.status === 'INVESTIGATING' ? 'bg-amber-500/10 text-amber-500' :
                        'bg-rose-500/10 text-rose-500'
                      )}>
                        {incident.status}
                      </span>
                    </td>
                    <td className="px-6 py-4">
                      <span className={cn(
                        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium",
                        incident.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-500' :
                        incident.severity === 'HIGH' ? 'bg-orange-500/10 text-orange-500' :
                        'bg-blue-500/10 text-blue-500'
                      )}>
                        {incident.severity}
                      </span>
                    </td>
                    <td className="px-6 py-4">{incident.source}</td>
                    <td className="px-6 py-4 whitespace-nowrap">{new Date(incident.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        
        {/* Basic Pagination Controls */}
        <div className="flex items-center justify-between border-t border-zinc-800 px-6 py-3">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0 || loading}
            className="rounded-md border border-zinc-700 px-3 py-1 text-sm text-zinc-300 hover:bg-zinc-800 disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-sm text-zinc-500">Page {page + 1}</span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={incidents.length < limit || loading}
            className="rounded-md border border-zinc-700 px-3 py-1 text-sm text-zinc-300 hover:bg-zinc-800 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default IncidentList;
