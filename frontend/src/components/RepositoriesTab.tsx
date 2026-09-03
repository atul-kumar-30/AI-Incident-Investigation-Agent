import React, { useState, useEffect } from 'react';
import type { Repository, RepositoryCreate } from '../types';
import { repositoryService } from '../services/repositoryService';

interface RepositoriesTabProps {
  incidentId: string;
}

const RepositoriesTab: React.FC<RepositoriesTabProps> = ({ incidentId }) => {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [repoName, setRepoName] = useState('');
  const [repoPath, setRepoPath] = useState('/app/demo_repositories');
  
  const loadRepositories = async () => {
    setLoading(true);
    try {
      const data = await repositoryService.getRepositories();
      setRepositories(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load repositories');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadRepositories();
  }, []);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!repoName || !repoPath) return;

    try {
      setLoading(true);
      setError(null);
      const repoCreate: RepositoryCreate = {
        name: repoName,
        source_type: 'LOCAL',
        source_location: repoPath
      };
      
      const newRepo = await repositoryService.createRepository(repoCreate);
      
      // Associate with incident
      await repositoryService.associateRepository(incidentId, newRepo.id);
      
      // Index repo
      await repositoryService.indexRepository(newRepo.id);
      
      setRepoName('');
      loadRepositories();
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to register repository');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-matrix-card/90 rounded-2xl border border-matrix-border overflow-hidden backdrop-blur shadow-sm">
      <div className="p-6 border-b border-matrix-border">
        <h3 className="text-base font-bold text-slate-100 mb-4 flex items-center gap-2 font-mono">
          <span className="w-2 h-2 rounded-full bg-emerald-400"></span>
          Code Repositories
        </h3>
        
        <form onSubmit={handleRegister} className="flex flex-col md:flex-row gap-4 items-end bg-matrix-surface/80 p-5 rounded-xl border border-matrix-border">
          <div className="flex-1 w-full">
            <label className="block text-xs font-mono text-slate-300 mb-1.5">Repository Identifier</label>
            <input 
              type="text" 
              value={repoName}
              onChange={e => setRepoName(e.target.value)}
              className="w-full px-3 py-2 bg-matrix-bg border border-matrix-border rounded-lg text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40 text-xs font-mono"
              placeholder="e.g. auth-service"
            />
          </div>
          <div className="flex-1 w-full">
            <label className="block text-xs font-mono text-slate-300 mb-1.5">Container Mount Path</label>
            <input 
              type="text" 
              value={repoPath}
              onChange={e => setRepoPath(e.target.value)}
              className="w-full px-3 py-2 bg-matrix-bg border border-matrix-border rounded-lg text-slate-100 placeholder:text-slate-500 focus:outline-none focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40 text-xs font-mono"
              placeholder="/app/demo_repositories/auth-service"
            />
          </div>
          <button 
            type="submit"
            disabled={loading || !repoName || !repoPath}
            className="w-full md:w-auto px-5 py-2 text-xs font-semibold font-mono rounded-lg text-black bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 shadow-matrix-glow focus:outline-none disabled:opacity-50 transition-all whitespace-nowrap"
          >
            {loading ? 'Indexing...' : 'Register & Index'}
          </button>
        </form>
        {error && <div className="mt-3 text-xs font-mono text-rose-400 bg-rose-950/20 p-2.5 rounded-lg border border-rose-500/30">{error}</div>}
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-matrix-border font-mono text-xs">
          <thead className="bg-matrix-surface/90 text-[11px] uppercase tracking-wider text-slate-400 border-b border-matrix-border">
            <tr>
              <th scope="col" className="px-6 py-3.5 text-left font-medium">Name</th>
              <th scope="col" className="px-6 py-3.5 text-left font-medium">Location</th>
              <th scope="col" className="px-6 py-3.5 text-left font-medium">Status</th>
              <th scope="col" className="px-6 py-3.5 text-left font-medium">Indexed At</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-matrix-border">
            {repositories.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-10 text-center text-xs text-slate-500">
                  No repositories registered for this incident.
                </td>
              </tr>
            ) : (
              repositories.map((repo) => (
                <tr key={repo.id} className="hover:bg-matrix-surface/50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap font-semibold text-emerald-400">{repo.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-slate-400">{repo.source_location}</td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2.5 py-0.5 inline-flex text-[10px] font-semibold rounded-full border
                      ${repo.ingestion_status === 'READY' ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30' : 
                        repo.ingestion_status === 'FAILED' ? 'bg-rose-500/15 text-rose-400 border-rose-500/30' : 
                        'bg-amber-500/15 text-amber-400 border-amber-500/30'}`}>
                      {repo.ingestion_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-slate-500">
                    {new Date(repo.updated_at).toLocaleString()}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default RepositoriesTab;
