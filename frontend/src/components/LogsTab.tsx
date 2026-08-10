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

  if (loading) return <div className="p-8 text-center text-zinc-500">Loading logs...</div>;
  if (error) return <div className="p-8 text-center text-red-500">{error}</div>;

  return (
    <div className="space-y-4">
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left">
            <thead className="text-xs text-zinc-400 uppercase bg-zinc-950/50 border-b border-zinc-800">
              <tr>
                <th className="px-4 py-3">Time</th>
                <th className="px-4 py-3">Level</th>
                <th className="px-4 py-3">Service</th>
                <th className="px-4 py-3">Endpoint</th>
                <th className="px-4 py-3">Status</th>
                <th className="px-4 py-3">Message</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/50">
              {logs.map((log) => (
                <tr key={log.id} className="hover:bg-zinc-800/20 text-zinc-300 font-mono text-xs">
                  <td className="px-4 py-2 whitespace-nowrap">{new Date(log.timestamp).toLocaleTimeString()}</td>
                  <td className="px-4 py-2">
                    <span className={cn(
                      "px-2 py-0.5 rounded text-[10px] font-medium",
                      log.level === 'ERROR' || log.level === 'CRITICAL' ? 'bg-red-500/20 text-red-400' :
                      log.level === 'WARN' ? 'bg-yellow-500/20 text-yellow-400' :
                      'bg-blue-500/20 text-blue-400'
                    )}>
                      {log.level}
                    </span>
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap">{log.service}</td>
                  <td className="px-4 py-2 whitespace-nowrap">{log.endpoint || '-'}</td>
                  <td className="px-4 py-2">{log.http_status || '-'}</td>
                  <td className="px-4 py-2 truncate max-w-md" title={log.message}>{log.message}</td>
                </tr>
              ))}
              {logs.length === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-8 text-center text-zinc-500">No logs found.</td>
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
