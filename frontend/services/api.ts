import axios from "axios";
import type { HealthResponse, InvestigateResponse } from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  timeout: 180000,
});

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get("/health");
  return data;
}

export async function runInvestigation(
  accessToken: string,
  investigationId: string,
  namespace?: string,
): Promise<InvestigateResponse> {
  const { data } = await api.post(
    "/investigate",
    { investigation_id: investigationId, namespace: namespace || null },
    { headers: { Authorization: `Bearer ${accessToken}` } },
  );
  return data;
}
