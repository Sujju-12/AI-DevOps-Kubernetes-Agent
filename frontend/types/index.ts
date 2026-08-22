export type ClusterContext = {
  name: string;
  cluster: string;
  user: string;
  namespace?: string | null;
  server?: string | null;
  is_current: boolean;
};

export type Diagnosis = {
  root_cause: string;
  explanation: string;
  fix: string;
  kubectl_command: string;
  prevention: string;
  confidence: number;
  engine: string;
};

export type InvestigationRecord = {
  id: string;
  timestamp: string;
  context?: string | null;
  namespace?: string | null;
  root_cause: string;
  confidence: number;
  status: string;
};

export type InvestigateResponse = {
  status: string;
  job_id: string;
  cluster_context?: string | null;
  investigation?: Record<string, unknown>;
  diagnosis?: Diagnosis | null;
  error?: string | null;
  history?: InvestigationRecord[];
};

export type ProgressEvent = {
  event: string;
  step?: string;
  label?: string;
  done?: boolean;
  message?: string;
  payload?: InvestigateResponse;
};
