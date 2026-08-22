import apiClient from './apiClient';

export interface InvestigationRequest {
  namespace?: string;
  investigation_type?: string;
}

export interface InvestigationResult {
  investigation_id: string;
  status: string;
  root_cause: string;
  confidence: number;
  suggested_fixes: Array<Record<string, any>>;
  timestamp: string;
}

export const investigationService = {
  async getStatus() {
    const response = await apiClient.get('/api/status');
    return response.data;
  },

  async startInvestigation(request: InvestigationRequest) {
    const response = await apiClient.post('/investigate', request);
    return response.data;
  },

  async getHealth() {
    const response = await apiClient.get('/health');
    return response.data;
  },
};
