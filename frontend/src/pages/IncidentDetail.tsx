import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { incidentService } from '../services/incidentService';
import { investigationService } from '../services/investigationService';
import type { Incident, IncidentStatus, InvestigationRun } from '../types';
import { cn } from '../utils';
import { Terminal, Clock, Server, ArrowLeft, Trash2 } from 'lucide-react';
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
    return <div className="flex h-64 items-center justify-center"><div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div></div>;
  }

  if (error || !incident) {
    return <div className="rounded-md bg-red-500/10 p-4 text-red-500">{error}</div>;
  }

  return (
    <div className="space-y-6 max-w-5xl mx-auto">
      <button onClick={() => navigate(-1)} className="flex items-center text-sm text-zinc-400 hover:text-zinc-100 transition-colors">
        <ArrowLeft className="mr-1 h-4 w-4" /> Back
      </button>

      <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-zinc-100">{incident.title}</h1>
          <div className="mt-2 flex flex-wrap items-center gap-3 text-sm text-zinc-400">
            <span className="flex items-center gap-1"><Clock className="h-4 w-4" /> Created: {new Date(incident.created_at).toLocaleString()}</span>
            <span>•</span>
            <span className="flex items-center gap-1"><Server className="h-4 w-4" /> Source: {incident.source}</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button 
            onClick={handleStartInvestigation}
            disabled={investigating || investigation !== null}
            className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium rounded-md shadow-sm transition-colors"
          >
            {investigating ? 'Starting...' : investigation ? 'Investigating' : 'Start Investigation'}
          </button>
          <select 
            value={incident.status}
            onChange={(e) => handleStatusChange(e.target.value as IncidentStatus)}
            className="rounded-md border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-sm text-zinc-100 focus:outline-none focus:ring-1 focus:ring-indigo-500"
          >
            <option value="OPEN">Open</option>
            <option value="INVESTIGATING">Investigating</option>
            <option value="RESOLVED">Resolved</option>
            <option value="FAILED">Failed</option>
          </select>
          <span className={cn(
            "inline-flex items-center rounded-full px-3 py-1 text-sm font-medium",
            incident.severity === 'CRITICAL' ? 'bg-red-500/10 text-red-500' :
            incident.severity === 'HIGH' ? 'bg-orange-500/10 text-orange-500' :
            'bg-blue-500/10 text-blue-500'
          )}>
            {incident.severity}
          </span>
          <button onClick={handleDelete} className="p-2 text-red-500 hover:bg-red-500/10 rounded-md transition-colors" title="Delete Incident">
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>

      <div className="border-b border-zinc-800 mb-6">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('overview')}
            className={cn(
              "whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors",
              activeTab === 'overview'
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-zinc-400 hover:text-zinc-300 hover:border-zinc-700"
            )}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab('logs')}
            className={cn(
              "whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors",
              activeTab === 'logs'
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-zinc-400 hover:text-zinc-300 hover:border-zinc-700"
            )}
          >
            Logs
          </button>
          <button
            onClick={() => setActiveTab('repositories')}
            className={cn(
              "whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors",
              activeTab === 'repositories'
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-zinc-400 hover:text-zinc-300 hover:border-zinc-700"
            )}
          >
            Repositories
          </button>
          <button
            onClick={() => setActiveTab('documents')}
            className={cn(
              "whitespace-nowrap pb-4 px-1 border-b-2 font-medium text-sm transition-colors",
              activeTab === 'documents'
                ? "border-indigo-500 text-indigo-400"
                : "border-transparent text-zinc-400 hover:text-zinc-300 hover:border-zinc-700"
            )}
          >
            Documents
          </button>
        </nav>
      </div>

      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="md:col-span-2 space-y-6">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 shadow-sm">
            <h2 className="text-lg font-medium text-zinc-100 mb-4">Description</h2>
            <div className="prose prose-invert max-w-none text-zinc-300 whitespace-pre-wrap">
              {incident.description}
            </div>
          </div>

          {/* AI Investigation Area */}
          {investigation ? (
            <div className="md:col-span-3 mt-4">
              <InvestigationPanel run={investigation} />
            </div>
          ) : (
            <div className="rounded-xl border border-indigo-900/30 bg-indigo-950/10 p-6 shadow-sm relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1 h-full bg-indigo-600"></div>
              <div className="flex items-center gap-2 mb-4">
                <Terminal className="h-5 w-5 text-indigo-400" />
                <h2 className="text-lg font-medium text-indigo-100">AI Investigation</h2>
              </div>
              
              <div className="rounded-md border border-zinc-800 bg-zinc-950 p-6 text-center">
                <p className="text-zinc-400">No investigation has been started for this incident.</p>
                <p className="text-sm text-zinc-500 mt-2">Click the "Start Investigation" button above to launch the AI Agent.</p>
              </div>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-6 shadow-sm">
            <h3 className="text-sm font-medium text-zinc-100 mb-4 uppercase tracking-wider">Metadata</h3>
            <div className="space-y-4 text-sm">
              <div>
                <span className="block text-zinc-500">ID</span>
                <span className="font-mono text-zinc-300 break-all">{incident.id}</span>
              </div>
              <div>
                <span className="block text-zinc-500">Last Updated</span>
                <span className="text-zinc-300">{new Date(incident.updated_at).toLocaleString()}</span>
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
        <DocumentsTab incident={incident} apiBaseUrl="http://localhost:8000/api/v1" />
      )}
    </div>
  );
};

export default IncidentDetail;
