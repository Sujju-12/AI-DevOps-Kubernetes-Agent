import axios from "axios";
import type { ClusterContext, InvestigateResponse, InvestigationRecord } from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  timeout: 120000,
});

export function setToken(token: string | null) {
  if (token) {
    api.defaults.headers.common.Authorization = `Bearer ${token}`;
    if (typeof window !== "undefined") localStorage.setItem("token", token);
  } else {
    delete api.defaults.headers.common.Authorization;
    if (typeof window !== "undefined") localStorage.removeItem("token");
  }
}

export function loadToken(): string | null {
  if (typeof window === "undefined") return null;
  const token = localStorage.getItem("token");
  if (token) setToken(token);
  return token;
}

export async function login(username: string, password: string) {
  const { data } = await api.post("/auth/login", { username, password });
  setToken(data.access_token);
  return data as { access_token: string; username: string };
}

export async function fetchHealth() {
  const { data } = await api.get("/health");
  return data as { status: string; service: string; mode: string };
}

export async function fetchClusters() {
  const { data } = await api.get("/clusters");
  return data as {
    kubeconfig_path: string;
    current_context?: string | null;
    contexts: ClusterContext[];
    warning?: string | null;
  };
}

export async function fetchHistory() {
  const { data } = await api.get("/history");
  return data.items as InvestigationRecord[];
}

export async function investigate(context?: string) {
  const { data } = await api.post("/investigate", { context });
  return data as InvestigateResponse;
}

export { api };
