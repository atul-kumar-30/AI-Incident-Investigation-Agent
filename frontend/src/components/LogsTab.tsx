import { useState, useEffect } from 'react';
import { logService } from '../services/logService';
import type { LogEntry } from '../types';
import { cn } from '../utils';

interface LogsTabProps {
  incidentId: string;
}

const LogsTab = ({ incidentId }: LogsTabProps) => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        setLoading(true);
        const data = await logService.getLogs(incidentId, { limit: 100 });
        setLogs(data);
      } catch (err: any) {
        setError(err.message || 'Failed to fetch logs');
      } finally {
        setLoading(false);
      }
    };
    fetchLogs();
  }, [incidentId]);

  if (loading) return (
    <div className="flex h-48 items-center justify-center">
      <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-500/20 border-t-emerald-400"></div>
    </div>
  );
  if (error) return <div className="p-4 text-xs font-mono text-rose-400 bg-rose-950/20 rounded-xl border border-rose-500/30">{error}</div>;

  return (
    <div className="space-y-4">
      <div className="rounded-2xl border border-matrix-border bg-matrix-card/95 shadow-sm overflow-hidden backdrop-blur">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left font-mono">
            <thead className="text-[11px] text-slate-400 uppercase tracking-wider bg-matrix-surface/90 border-b border-matrix-border">
              <tr>
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3">Level</th>
                <th className="px-4 py-3">Service</th>
                <th className="px-4 py-3">Endpoint</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-matrix-border">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-matrix-surface/50 text-slate-300 text-xs transition-colors">
                  <td className="px-4 py-2.5 whitespace-nowrap text-slate-500">{new Date(log.timestamp).toLocaleTimeString()}</td>
                  <td className="px-4 py-2.5">
                    <span className={cn(
                      "px-2 py-0.5 rounded text-[10px] font-medium border",
                      log.level === 'ERROR' || log.level === 'CRITICAL' ? 'bg-rose-500/15 text-rose-400 border-rose-500/30' :
                      log.level === 'WARN' ? 'bg-amber-500/15 text-amber-400 border-amber-500/30' :
                      'bg-cyan-500/15 text-cyan-400 border-cyan-500/30'
                    )}>
                      {log.level}
                    </span>
                  </td>
                  <td className="px-4 py-2.5 whitespace-nowrap text-emerald-400 font-semibold">{log.service}</td>
                  <td className="px-4 py-2.5 whitespace-nowrap text-slate-400">{log.endpoint || '-'}</td>
                  <td className="px-4 py-2.5 text-slate-300">{log.http_status || '-'}</td>
                  <td className="px-4 py-2.5 truncate max-w-md text-slate-300" title={log.message}>{log.message}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-12 text-center text-slate-500 text-xs">
                    No log events recorded for this incident yet.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default LogsTab;
