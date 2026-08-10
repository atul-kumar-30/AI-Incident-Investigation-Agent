import type { Hypothesis, HypothesisEvidenceMapping } from '../types';

const API_BASE_URL = 'http://localhost:8000/api/v1';

export const hypothesisService = {
  async getInvestigationHypotheses(runId: string): Promise<Hypothesis[]> {
    const response = await fetch(`${API_BASE_URL}/investigations/${runId}/hypotheses`);
    if (!response.ok) {
      throw new Error('Failed to fetch hypotheses');
    }
    return response.json();
  },

  async getHypothesis(hypothesisId: string): Promise<Hypothesis> {
    const response = await fetch(`${API_BASE_URL}/hypotheses/${hypothesisId}`);
    if (!response.ok) {
      throw new Error('Failed to fetch hypothesis');
    }
    return response.json();
  },

  async getHypothesisEvidence(hypothesisId: string): Promise<HypothesisEvidenceMapping[]> {
    const response = await fetch(`${API_BASE_URL}/hypotheses/${hypothesisId}/evidence`);
    if (!response.ok) {
      throw new Error('Failed to fetch hypothesis evidence');
    }
    return response.json();
  },

  async verifyHypothesis(hypothesisId: string): Promise<{status: string, verification_id: string}> {
    const response = await fetch(`${API_BASE_URL}/hypotheses/${hypothesisId}/verify`, {
      method: 'POST'
    });
    if (!response.ok) {
      throw new Error('Failed to verify hypothesis');
    }
    return response.json();
  },

  async getVerifications(hypothesisId: string): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/hypotheses/${hypothesisId}/verifications`);
    if (!response.ok) {
      throw new Error('Failed to fetch verifications');
    }
    return response.json();
  },

  async getVerificationSteps(verificationId: string): Promise<any[]> {
    const response = await fetch(`${API_BASE_URL}/verifications/${verificationId}/steps`);
    if (!response.ok) {
      throw new Error('Failed to fetch verification steps');
    }
    return response.json();
  }
};
