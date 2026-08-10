import api from './api';
import type { LogEntry } from '../types';

export const logService = {
  getLogs: async (
    incidentId: string,
    params?: {
      query?: string;
      levels?: string[];
      services?: string[];
      endpoint?: string;
      http_status?: number;
      limit?: number;
    }
  ): Promise<LogEntry[]> => {
    // Convert array params to comma separated strings or URLSearchParams compatible format
    let queryParams = '';
    if (params) {
      const searchParams = new URLSearchParams();
      if (params.query) searchParams.append('query', params.query);
      if (params.levels) params.levels.forEach(l => searchParams.append('levels', l));
      if (params.services) params.services.forEach(s => searchParams.append('services', s));
      if (params.endpoint) searchParams.append('endpoint', params.endpoint);
      if (params.http_status) searchParams.append('http_status', params.http_status.toString());
      if (params.limit) searchParams.append('limit', params.limit.toString());
      
      const str = searchParams.toString();
      if (str) queryParams = `?${str}`;
    }
    
    const response = await api.get(`/incidents/${incidentId}/logs${queryParams}`);
    return response.data;
  }
};
