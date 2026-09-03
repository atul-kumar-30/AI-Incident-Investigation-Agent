import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { incidentService } from '../services/incidentService';
import { investigationService } from '../services/investigationService';
import type { Incident, IncidentStatus, InvestigationRun } from '../types';
import { cn } from '../utils';
import { Terminal, Clock, Server, ArrowLeft, Trash2, Play } from 'lucide-react';
import InvestigationPanel from '../components/InvestigationPanel';
import LogsTab from '../components/LogsTab';
import RepositoriesTab from '../components/RepositoriesTab';
import { DocumentsTab } from '../components/DocumentsTab';

const IncidentDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [investigation, setInvestigation] = useState<InvestigationRun | null>(null);
  const [loading, setLoading] = useState(true);
  const [investigating, setInvestigating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'logs' | 'repositories' | 'documents'>('overview');

  useEffect(() => {
    const loadIncident = async () => {
      try {
        setLoading(true);
        const data = await incidentService.getIncident(id!);
        setIncident(data);
      } catch (err) {
        setError('Incident not found or failed to load.');
      } finally {
        setLoading(false);
      }
    };

    if (id) {
      loadIncident();
    }
  }, [id]);

  const handleStartInvestigation = async () => {
    if (!id) return;
    setInvestigating(true);
    try {
      const run = await investigationService.startInvestigation(id);
      setInvestigation(run);
      setIncident(prev => prev ? { ...prev, status: 'INVESTIGATING' } : prev);
    } catch (err: any) {
      console.error(err);
      setError(`Failed to start investigation: ${err.message}`);
    } finally {
      setInvestigating(false);
    }
  };

  const handleStatusChange = async (status: IncidentStatus) => {
    try {
      if (incident) {
        const updated = await incidentService.updateIncident(incident.id, { status });
        setIncident(updated);
      }
    } catch (err) {
      alert("Failed to update status");
    }
  };
  
  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this incident?')) {
      try {
        if (incident) {
          await incidentService.deleteIncident(incident.id);
          navigate('/incidents');
        }
      } catch (err) {
        alert("Failed to delete incident");
      }
    }
  };

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

  if (error || !incident) {
    return (
      <div className="rounded-xl border border-rose-500/30 bg-rose-950/20 p-4 text-rose-400 font-mono text-sm">
        {error}
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <button 
        onClick={() => navigate(-1)} 
        className="inline-flex items-center text-xs font-mono text-slate-400 hover:text-emerald-400 transition-colors"
      >
        <ArrowLeft className="mr-1.5 h-3.5 w-3.5" /> Return to Incidents
      </button>

      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-3xl font-extrabold tracking-tight text-slate-100">{incident.title}</h1>
            <span className={cn(
              "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-mono font-medium border",
              incident.severity === 'CRITICAL' ? 'bg-rose-500/15 text-rose-400 border-rose-500/30' :
              incident.severity === 'HIGH' ? 'bg-amber-500/15 text-amber-400 border-amber-500/30' :
              'bg-slate-500/15 text-slate-400 border-slate-500/30'
            )}>
              {incident.severity}
            </span>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-3 text-xs font-mono text-slate-400">
            <span className="flex items-center gap-1.5"><Clock className="h-3.5 w-3.5 text-slate-500" /> Created: {new Date(incident.created_at).toLocaleString()}</span>
            <span>•</span>
            <span className="flex items-center gap-1.5"><Server className="h-3.5 w-3.5 text-slate-500" /> Source: {incident.source}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={handleStartInvestigation}
            disabled={investigating || investigation !== null}
            className={cn(
              "px-4 py-2 text-sm font-semibold rounded-lg shadow-matrix-glow transition-all flex items-center gap-2",
              investigation
                ? "bg-emerald-950/40 text-emerald-400 border border-emerald-500/40 cursor-default"
                : investigating
                ? "bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse"
                : "bg-gradient-to-r from-emerald-500 to-teal-500 text-black hover:from-emerald-400 hover:to-teal-400"
            )}
          >
            <Play className="h-4 w-4" />
            {investigating ? 'Running AI Agent...' : investigation ? 'Investigation Active' : 'Start Investigation'}
          </button>
          <select 
            value={incident.status}
            onChange={(e) => handleStatusChange(e.target.value as IncidentStatus)}
            className="rounded-lg border border-matrix-border bg-matrix-surface px-3 py-2 text-xs font-mono text-slate-200 focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40"
          >
            <option value="OPEN" className="bg-matrix-surface">OPEN</option>
            <option value="INVESTIGATING" className="bg-matrix-surface">INVESTIGATING</option>
            <option value="RESOLVED" className="bg-matrix-surface">RESOLVED</option>
            <option value="FAILED" className="bg-matrix-surface">FAILED</option>
          </select>
          <button 
            onClick={handleDelete} 
            className="p-2 text-rose-400 hover:bg-rose-500/10 hover:text-rose-300 rounded-lg border border-transparent hover:border-rose-500/20 transition-colors" 
            title="Delete Incident"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="border-b border-matrix-border mb-6">
        <nav className="-mb-px flex space-x-8">
          {[
            { id: 'overview', label: 'Overview' },
            { id: 'logs', label: 'Log Stream' },
            { id: 'repositories', label: 'Repositories & Code' },
            { id: 'documents', label: 'Runbooks & Fix Guides' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={cn(
                "whitespace-nowrap pb-3.5 px-1 border-b-2 text-sm font-medium transition-all duration-200 font-mono",
                activeTab === tab.id
                  ? "border-emerald-400 text-emerald-300 font-semibold shadow-[0_1px_12px_rgba(16,185,129,0.35)]"
                  : "border-transparent text-slate-400 hover:text-slate-200 hover:border-slate-700"
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="rounded-2xl border border-matrix-border bg-matrix-card/90 p-6 shadow-sm backdrop-blur">
              <h2 className="text-base font-semibold text-slate-100 mb-3">Incident Summary</h2>
              <div className="prose prose-invert max-w-none text-slate-300 text-sm whitespace-pre-wrap leading-relaxed">
                {incident.description}
              </div>
            </div>

            {/* AI Investigation Area */}
            {investigation ? (
              <div className="mt-4">
                <InvestigationPanel run={investigation} />
              </div>
            ) : (
              <div className="rounded-2xl border border-emerald-500/20 bg-emerald-950/10 p-8 shadow-matrix-glow-sm relative overflow-hidden backdrop-blur">
                <div className="absolute top-0 left-0 w-1.5 h-full bg-gradient-to-b from-emerald-400 to-teal-600"></div>
                <div className="flex items-center gap-2.5 mb-4">
                  <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
                    <Terminal className="h-5 w-5 text-emerald-400" />
                  </div>
                  <div>
                    <h2 className="text-base font-semibold text-slate-100">Automated AI Investigation</h2>
                    <p className="text-xs font-mono text-slate-400">Autonomous planning, multi-source evidence retrieval & verification</p>
                  </div>
                </div>
                
                <div className="rounded-xl border border-matrix-border bg-matrix-surface/80 p-8 text-center">
                  <p className="text-sm text-slate-300">Ready to initiate full multi-vector investigation.</p>
                  <p className="text-xs font-mono text-emerald-400/80 mt-2">
                    Click the "Start Investigation" button above to launch the autonomous LangGraph agent.
                  </p>
                </div>
              </div>
            )}
          </div>

          <div className="space-y-6">
            <div className="rounded-2xl border border-matrix-border bg-matrix-card/90 p-6 shadow-sm backdrop-blur">
              <h3 className="text-xs font-mono font-medium text-emerald-400 mb-4 uppercase tracking-wider flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                Incident Telemetry
              </h3>
              <div className="space-y-4 text-xs font-mono">
                <div>
                  <span className="block text-slate-500 mb-0.5">UUID</span>
                  <span className="text-slate-300 select-all break-all bg-matrix-surface px-2 py-1 rounded border border-matrix-border block">{incident.id}</span>
                </div>
                <div>
                  <span className="block text-slate-500 mb-0.5">Status</span>
                  <span className="text-slate-200">{incident.status}</span>
                </div>
                <div>
                  <span className="block text-slate-500 mb-0.5">Severity</span>
                  <span className="text-slate-200">{incident.severity}</span>
                </div>
                <div>
                  <span className="block text-slate-500 mb-0.5">Last Updated</span>
                  <span className="text-slate-300">{new Date(incident.updated_at).toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
      
      {activeTab === 'logs' && (
        <LogsTab incidentId={incident.id} />
      )}
      
      {activeTab === 'repositories' && (
        <RepositoriesTab incidentId={incident.id} />
      )}
      
      {activeTab === 'documents' && (
        <DocumentsTab incident={incident} apiBaseUrl={import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'} />
      )}
    </div>
  );
};

export default IncidentDetail;
