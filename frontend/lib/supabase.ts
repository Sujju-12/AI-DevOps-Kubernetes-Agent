import { createClient, type SupabaseClient } from "@supabase/supabase-js";

/** Project tzdxvhbdpkqckkmecytz — publishable values (RLS still applies). */
const DEFAULT_SUPABASE_URL = "https://tzdxvhbdpkqckkmecytz.supabase.co";
const DEFAULT_SUPABASE_ANON_KEY =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR6ZHh2aGJkcGtxY2trbWVjeXR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc0NTk4NzUsImV4cCI6MjEwMzAzNTg3NX0.l45EW90Z7QhEdGZfLTiTwUdcyyYY0YCv9UK0iQRYtsY";

function supabaseUrl(): string {
  return process.env.NEXT_PUBLIC_SUPABASE_URL || DEFAULT_SUPABASE_URL;
}

function supabaseAnonKey(): string {
  return process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY || DEFAULT_SUPABASE_ANON_KEY;
}

let client: SupabaseClient | null = null;

export function isSupabaseConfigured(): boolean {
  return Boolean(supabaseUrl() && supabaseAnonKey());
}

export function getSupabase(): SupabaseClient {
  if (client) {
    return client;
  }
  client = createClient(supabaseUrl(), supabaseAnonKey());
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
