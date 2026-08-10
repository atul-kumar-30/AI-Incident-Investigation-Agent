import api from './api';
import type { InvestigationRun, InvestigationStep, Evidence } from '../types';

export const investigationService = {
  startInvestigation: async (incidentId: string): Promise<InvestigationRun> => {
    const response = await api.post(`/incidents/${incidentId}/investigations`);
    return response.data;
  },

  getInvestigation: async (runId: string): Promise<InvestigationRun> => {
    const response = await api.get(`/investigations/${runId}`);
    return response.data;
  },

  getInvestigationSteps: async (runId: string): Promise<InvestigationStep[]> => {
    const response = await api.get(`/investigations/${runId}/steps`);
    return response.data;
  },

  getInvestigationEvidence: async (runId: string): Promise<Evidence[]> => {
    const response = await api.get(`/investigations/${runId}/evidence`);
    return response.data;
  }
};
