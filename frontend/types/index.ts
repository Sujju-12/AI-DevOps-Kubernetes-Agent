export type HealthResponse = {
  status: string;
  service: string;
};

export type InvestigateResponse = {
  status: string;
  investigation: Record<string, unknown>;
  diagnosis?: {
    root_cause: string;
    explanation: string;
    fix: string;
    kubectl_command: string;
    confidence: number;
  } | null;
  message?: string | null;
};
