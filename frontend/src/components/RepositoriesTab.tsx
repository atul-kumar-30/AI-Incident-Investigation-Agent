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
    <div className="bg-white rounded-lg border border-slate-200 overflow-hidden">
      <div className="p-4 border-b border-slate-200">
        <h3 className="text-lg font-medium text-slate-900 mb-4">Code Repositories</h3>
        
        <form onSubmit={handleRegister} className="flex gap-4 items-end bg-slate-50 p-4 rounded-md border border-slate-200">
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-700 mb-1">Repository Name</label>
            <input 
              type="text" 
              value={repoName}
              onChange={e => setRepoName(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="e.g. backend-api"
            />
          </div>
          <div className="flex-1">
            <label className="block text-sm font-medium text-slate-700 mb-1">Local Path (Inside Container)</label>
            <input 
              type="text" 
              value={repoPath}
              onChange={e => setRepoPath(e.target.value)}
              className="w-full px-3 py-2 border border-slate-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm"
              placeholder="/app/demo_repositories/my-repo"
            />
          </div>
          <button 
            type="submit"
            disabled={loading || !repoName || !repoPath}
            className="px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50"
          >
            Register & Index
          </button>
        </form>
        {error && <div className="mt-2 text-sm text-red-600">{error}</div>}
      </div>
      
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200">
          <thead className="bg-slate-50">
            <tr>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Name</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Location</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Status</th>
              <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-slate-500 uppercase tracking-wider">Indexed At</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-slate-200">
            {repositories.length === 0 ? (
              <tr>
                <td colSpan={4} className="px-6 py-4 text-center text-sm text-slate-500">
                  No repositories registered.
                </td>
              </tr>
            ) : (
              repositories.map((repo) => (
                <tr key={repo.id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-slate-900">{repo.name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">{repo.source_location}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
                    <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full 
                      ${repo.ingestion_status === 'READY' ? 'bg-green-100 text-green-800' : 
                        repo.ingestion_status === 'FAILED' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'}`}>
                      {repo.ingestion_status}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-slate-500">
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
