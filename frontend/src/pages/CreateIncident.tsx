import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { incidentService } from '../services/incidentService';
import type { IncidentSeverity } from '../types';

const CreateIncident = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    severity: 'HIGH' as IncidentSeverity,
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setLoading(true);
      setError(null);
      const incident = await incidentService.createIncident(formData);
      navigate(`/incidents/${incident.id}`);
    } catch (err) {
      const error = err as any;
      setError(error.response?.data?.detail || 'Failed to create incident');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-extrabold tracking-tight text-transparent bg-clip-text bg-gradient-to-r from-slate-100 via-slate-200 to-emerald-400">
          Report Incident
        </h1>
        <p className="text-sm font-mono text-slate-400 mt-1">
          Provide initial telemetry & context for the AI investigation agent.
        </p>
      </div>

      <div className="rounded-2xl border border-matrix-border bg-matrix-card/90 p-8 shadow-sm backdrop-blur">
        {error && (
          <div className="mb-6 rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-sm font-mono text-rose-400">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-2">
            <label htmlFor="title" className="text-sm font-medium text-slate-300">Incident Title</label>
            <input
              id="title"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full rounded-lg border border-matrix-border bg-matrix-surface px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40 transition-colors"
              placeholder="e.g. Login requests returning HTTP 500"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="description" className="text-sm font-medium text-slate-300">Description & Observations</label>
            <textarea
              id="description"
              required
              rows={4}
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              className="w-full rounded-lg border border-matrix-border bg-matrix-surface px-4 py-2.5 text-sm text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40 transition-colors font-sans"
              placeholder="Detailed description of the issue, symptoms, affected services, and runtime impact."
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="severity" className="text-sm font-medium text-slate-300">Severity Level</label>
            <select
              id="severity"
              value={formData.severity}
              onChange={(e) => setFormData({ ...formData, severity: e.target.value as IncidentSeverity })}
              className="w-full rounded-lg border border-matrix-border bg-matrix-surface px-4 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40 transition-colors"
            >
              <option value="LOW" className="bg-matrix-surface text-slate-100">Low - Minor impact</option>
              <option value="MEDIUM" className="bg-matrix-surface text-slate-100">Medium - Degraded service</option>
              <option value="HIGH" className="bg-matrix-surface text-slate-100">High - Critical workflow impacted</option>
              <option value="CRITICAL" className="bg-matrix-surface text-slate-100">Critical - Total system outage</option>
            </select>
          </div>

          <div className="pt-4 flex justify-end gap-3 border-t border-matrix-border">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="rounded-lg border border-matrix-border bg-matrix-surface px-4 py-2 text-sm font-medium text-slate-300 hover:bg-matrix-cardHover transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="rounded-lg bg-gradient-to-r from-emerald-500 to-teal-500 px-6 py-2 text-sm font-semibold text-black shadow-matrix-glow hover:from-emerald-400 hover:to-teal-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 focus:ring-offset-matrix-bg disabled:opacity-50 transition-all duration-200"
            >
              {loading ? 'Initializing Agent...' : 'Create Incident'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateIncident;
