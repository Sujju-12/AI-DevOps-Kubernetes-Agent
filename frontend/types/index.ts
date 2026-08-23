export type HealthResponse = {
  status: string;
  service: string;
};

export type ClusterContext = {
  name: string;
  cluster: string | null;
  user: string | null;
  namespace: string | null;
  server: string | null;
  is_current: boolean;
};

export type ClusterListResponse = {
  status: string;
  current_context: string | null;
  kubeconfig_path: string;
  clusters: ClusterContext[];
  message?: string | null;
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
