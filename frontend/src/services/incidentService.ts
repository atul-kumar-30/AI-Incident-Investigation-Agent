import api from './api';
import type { Incident, IncidentCreate, IncidentUpdate } from '../types';

export const incidentService = {
  getIncidents: async (skip: number = 0, limit: number = 100): Promise<Incident[]> => {
    const response = await api.get('/incidents', { params: { skip, limit } });
    return response.data;
  },

  getIncident: async (id: string): Promise<Incident> => {
    const response = await api.get(`/incidents/${id}`);
    return response.data;
  },

  createIncident: async (data: IncidentCreate): Promise<Incident> => {
    const response = await api.post('/incidents', data);
    return response.data;
  },

  updateIncident: async (id: string, data: IncidentUpdate): Promise<Incident> => {
    const response = await api.patch(`/incidents/${id}`, data);
    return response.data;
  },

  deleteIncident: async (id: string): Promise<void> => {
    await api.delete(`/incidents/${id}`);
  },

  getHealth: async (): Promise<{ status: string, service: string }> => {
    const response = await api.get('/health');
    return response.data;
  }
};
