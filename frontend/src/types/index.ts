export interface Investigation {
  investigation_id: string;
  status: string;
  root_cause: string;
  confidence: number;
  suggested_fixes: Array<Record<string, any>>;
  timestamp: string;
}

export interface SystemStatus {
  status: string;
  service: string;
}
