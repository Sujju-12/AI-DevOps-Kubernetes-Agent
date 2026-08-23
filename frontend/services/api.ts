import axios from "axios";
import type { HealthResponse } from "@/types";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
  timeout: 10000,
});

export async function fetchHealth(): Promise<HealthResponse> {
  const { data } = await api.get("/health");
  return data;
}
