import axios from "axios";
import type { ClusterListResponse, HealthResponse, InvestigateResponse } from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  timeout: 180000,
});

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get("/health");
  return data;
}

export async function fetchClusters(): Promise<ClusterListResponse> {
  const { data } = await api.get("/clusters");
  return data;
}

export async function runInvestigation(
  accessToken: string,
  investigationId: string,
  options?: { namespace?: string; context?: string },
): Promise<InvestigateResponse> {
  const { data } = await api.post(
    "/investigate",
    {
      investigation_id: investigationId,
      namespace: options?.namespace || null,
      context: options?.context || null,
      cluster: options?.context || null,
    },
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  if (data?.status === "error") {
    throw new Error(data.message || "Investigation failed.");
  }
  return data;
}
