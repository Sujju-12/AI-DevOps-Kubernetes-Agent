"use client";

import { useEffect, useMemo, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { useHealth } from "@/hooks/useHealth";
import { DEFAULT_STEPS, getSupabase, type InvestigationRow } from "@/lib/supabase";
import { runInvestigation } from "@/services/api";

export function Dashboard({ session }: { session: Session }) {
  const health = useHealth();
  const ready = health.data?.status === "healthy";
  const [namespace, setNamespace] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState<InvestigationRow | null>(null);
  const [history, setHistory] = useState<InvestigationRow[]>([]);
  const supabase = useMemo(() => getSupabase(), []);
  const userId = session.user.id;

  useEffect(() => {
    let ignore = false;
    async function loadHistory() {
      const { data } = await supabase
        .from("investigations")
        .select("*")
        .eq("user_id", userId)
        .order("created_at", { ascending: false })
        .limit(8);
      if (!ignore) {
        setHistory((data as InvestigationRow[]) || []);
      }
    }
    loadHistory();
    const channel = supabase
      .channel("investigations-live")
      .on(
        "postgres_changes",
        { event: "*", schema: "public", table: "investigations", filter: `user_id=eq.${userId}` },
        (payload) => {
          const row = payload.new as InvestigationRow;
          if (!row?.id) {
            return;
          }
          setActive((current) => (current && current.id === row.id ? row : current));
          setHistory((items) => {
            const others = items.filter((item) => item.id !== row.id);
            return [row, ...others].slice(0, 8);
          });
        },
      )
      .subscribe();
    return () => {
      ignore = true;
      supabase.removeChannel(channel);
    };
  }, [supabase, userId]);

  async function onInvestigate() {
    setError("");
    setBusy(true);
    const { data, error: insertError } = await supabase
      .from("investigations")
      .insert({
        user_id: userId,
        status: "running",
        namespace: namespace || null,
        steps: DEFAULT_STEPS,
        current_step: "pods",
      })
      .select("*")
      .single();
    if (insertError || !data) {
      setBusy(false);
      setError(insertError?.message || "Could not start investigation.");
      return;
    }
    const row = data as InvestigationRow;
    setActive(row);
    try {
      await runInvestigation(session.access_token, row.id, namespace || undefined);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Investigation request failed.");
    } finally {
      setBusy(false);
    }
  }

  const steps = active?.steps?.length ? active.steps : DEFAULT_STEPS;
  const diagnosisReady = active?.status === "success" && active.root_cause;

  return (
    <main className="mx-auto min-h-screen max-w-2xl px-6 py-12">
      <header className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold tracking-tight">AI Kubernetes Agent</h1>
          <p className="mt-1 text-sm text-slate-400">
            System Status: {health.isLoading ? "Checking" : ready ? "Ready" : "Unavailable"}
          </p>
        </div>
        <button
          type="button"
          className="text-sm text-slate-400 hover:text-slate-200"
          onClick={() => supabase.auth.signOut()}
        >
          Sign out
        </button>
      </header>

      <div className="mt-8 flex flex-col gap-3 sm:flex-row">
        <input
          className="flex-1 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
          placeholder="Namespace (optional, default all)"
          value={namespace}
          onChange={(event) => setNamespace(event.target.value)}
        />
        <button
          type="button"
          onClick={onInvestigate}
          disabled={busy}
          className="rounded-xl bg-sky-500 px-6 py-3 font-semibold text-slate-950 disabled:opacity-60"
        >
          {busy ? "Investigating..." : "Investigate Cluster"}
        </button>
      </div>
      {error ? <p className="mt-3 text-sm text-rose-400">{error}</p> : null}

      <section className="mt-10">
        <h2 className="text-lg font-medium">Investigation Status</h2>
        <ul className="mt-3 space-y-2 text-slate-300">
          {steps.map((step) => (
            <li key={step.key}>
              {step.done ? "✓" : busy && active?.current_step === step.key ? "…" : "○"} {step.label}
            </li>
          ))}
        </ul>
      </section>

      {active?.status === "error" && active.message ? (
        <p className="mt-6 whitespace-pre-wrap text-sm text-amber-300">{active.message}</p>
      ) : null}

      {diagnosisReady ? (
        <section className="mt-10 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <h2 className="text-lg font-medium">Diagnosis</h2>
          <p className="mt-4 text-sm uppercase tracking-wide text-slate-500">Root Cause</p>
          <p className="text-lg">{active.root_cause}</p>
          <p className="mt-4 text-sm uppercase tracking-wide text-slate-500">Explanation</p>
          <p className="text-slate-300">{active.explanation}</p>
          <p className="mt-4 text-sm uppercase tracking-wide text-slate-500">Suggested Fix</p>
          <p className="text-slate-300">{active.fix}</p>
          <p className="mt-4 text-sm uppercase tracking-wide text-slate-500">Command</p>
          <pre className="mt-1 overflow-x-auto rounded bg-slate-950 p-3 text-sm text-sky-300">
            {active.kubectl_command}
          </pre>
          <p className="mt-4 text-slate-300">
            Confidence: <span className="font-semibold">{active.confidence}%</span>
          </p>
        </section>
      ) : null}

      <section className="mt-10">
        <h2 className="text-lg font-medium">Recent Investigations</h2>
        <ul className="mt-3 space-y-2 text-slate-300">
          {history.length === 0 ? (
            <li className="text-slate-500">No investigations yet.</li>
          ) : (
            history.map((item) => (
              <li key={item.id} className="flex justify-between gap-3 border-b border-slate-800 py-2">
                <span>{item.root_cause || item.status}</span>
                <span className="text-sm text-slate-500">
                  {item.confidence ? `${item.confidence}%` : item.status}
                </span>
              </li>
            ))
          )}
        </ul>
      </section>
    </main>
  );
}
