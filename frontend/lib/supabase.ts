import { createClient, type SupabaseClient } from "@supabase/supabase-js";

let client: SupabaseClient | null = null;

export function isSupabaseConfigured(): boolean {
  return Boolean(process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY);
}

export function getSupabase(): SupabaseClient {
  if (client) {
    return client;
  }
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL || "";
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || "";
  if (!url || !anonKey) {
    throw new Error("Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY");
  }
  client = createClient(url, anonKey);
  return client;
}

export const DEFAULT_STEPS = [
  { key: "pods", label: "Checking Pods", done: false },
  { key: "logs", label: "Reading Logs", done: false },
  { key: "events", label: "Analyzing Events", done: false },
  { key: "deployments", label: "Inspecting Deployments", done: false },
  { key: "network", label: "Checking Networking", done: false },
  { key: "ai", label: "AI Reasoning", done: false },
  { key: "done", label: "Root Cause Found", done: false },
];

export type InvestigationRow = {
  id: string;
  created_at: string;
  status: string;
  current_step: string | null;
  steps: { key: string; label: string; done: boolean }[];
  namespace: string | null;
  cluster: string | null;
  root_cause: string | null;
  explanation: string | null;
  fix: string | null;
  kubectl_command: string | null;
  confidence: number | null;
  message: string | null;
};
