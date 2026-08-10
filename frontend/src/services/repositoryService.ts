import api from './api';
import type { Repository, RepositoryCreate } from '../types';

export const repositoryService = {
  getRepositories: async (): Promise<Repository[]> => {
    const response = await api.get('/repositories');
    return response.data;
  },

  getRepository: async (id: string): Promise<Repository> => {
    const response = await api.get(`/repositories/${id}`);
    return response.data;
  },

  createRepository: async (data: RepositoryCreate): Promise<Repository> => {
    const response = await api.post('/repositories', data);
    return response.data;
  },

  associateRepository: async (incidentId: string, repositoryId: string): Promise<void> => {
    await api.post(`/incidents/${incidentId}/repositories/${repositoryId}`);
  },

  indexRepository: async (repositoryId: string): Promise<void> => {
    await api.post(`/repositories/${repositoryId}/index`);
  }
};
