"use client";

import { useEffect, useMemo, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { useHealth } from "@/hooks/useHealth";
import { CLUSTER_HEALTHY, friendlyApiError, friendlyAuthError } from "@/lib/errors";
import { DEFAULT_STEPS, getSupabase, type InvestigationRow } from "@/lib/supabase";
import { fetchClusters, runInvestigation } from "@/services/api";
import type { ClusterContext } from "@/types";

export function Dashboard({ session }: { session: Session }) {
  const health = useHealth();
  const ready = health.data?.status === "healthy";
  const [namespace, setNamespace] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [active, setActive] = useState<InvestigationRow | null>(null);
  const [history, setHistory] = useState<InvestigationRow[]>([]);
  const [clusters, setClusters] = useState<ClusterContext[]>([]);
  const [clustersMessage, setClustersMessage] = useState("");
  const [selectedContext, setSelectedContext] = useState<string | null>(null);
  const supabase = useMemo(() => getSupabase(), []);
  const userId = session.user.id;

  useEffect(() => {
    let ignore = false;
    async function loadClusters() {
      try {
        const data = await fetchClusters();
        if (ignore) {
          return;
        }
        if (data.status !== "success") {
          setClusters([]);
          setClustersMessage(data.message || "Unable to list clusters from kubeconfig.");
          return;
        }
        setClusters(data.clusters || []);
        setClustersMessage("");
        const current = data.clusters.find((item) => item.is_current) || data.clusters[0];
        setSelectedContext((previous) => previous || current?.name || null);
      } catch (err) {
        if (!ignore) {
          setClustersMessage(friendlyApiError(err));
        }
      }
    }
    loadClusters();
    return () => {
      ignore = true;
    };
  }, []);

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

  async function investigateContext(contextName: string) {
    setSelectedContext(contextName);
    setError("");
    setBusy(true);
    const { data, error: insertError } = await supabase
      .from("investigations")
      .insert({
        user_id: userId,
        status: "running",
        namespace: namespace || null,
        cluster: contextName,
        steps: DEFAULT_STEPS,
        current_step: "pods",
      })
      .select("*")
      .single();
    if (insertError || !data) {
      setBusy(false);
      setError(friendlyAuthError(insertError?.message || "Could not start investigation."));
      return;
    }
    const row = data as InvestigationRow;
    setActive(row);
    try {
      await runInvestigation(session.access_token, row.id, {
        namespace: namespace || undefined,
        context: contextName,
      });
    } catch (err) {
      setError(friendlyApiError(err));
    } finally {
      setBusy(false);
    }
  }

  const steps = active?.steps?.length ? active.steps : DEFAULT_STEPS;
  const healthy =
    active?.status === "success" &&
    Boolean(active.root_cause?.includes("No critical Kubernetes issues"));
  const diagnosisReady = active?.status === "success" && active.root_cause && !healthy;
  const investigating = busy || active?.status === "running";

  return (
    <main className="mx-auto min-h-screen max-w-3xl px-6 py-12">
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

      <section className="mt-8">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-lg font-medium">Kubernetes Clusters</h2>
          <input
            className="w-56 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm"
            placeholder="Namespace (optional)"
            value={namespace}
            onChange={(event) => setNamespace(event.target.value)}
          />
        </div>
        <p className="mt-1 text-sm text-slate-500">
          Click a cluster from your kubeconfig to investigate it.
        </p>
        {clustersMessage ? (
          <p className="mt-3 whitespace-pre-wrap text-sm text-amber-300">{clustersMessage}</p>
        ) : null}
        <ul className="mt-4 grid gap-3">
          {clusters.length === 0 && !clustersMessage ? (
            <li className="text-slate-500">No clusters found in kubeconfig.</li>
          ) : (
            clusters.map((item) => {
              const selected = selectedContext === item.name;
              return (
                <li key={item.name}>
                  <button
                    type="button"
                    disabled={busy}
                    onClick={() => investigateContext(item.name)}
                    className={`w-full rounded-xl border px-4 py-3 text-left transition ${
                      selected
                        ? "border-sky-400 bg-sky-500/10"
                        : "border-slate-800 bg-slate-900/50 hover:border-slate-600"
                    } disabled:opacity-60`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-medium">{item.name}</span>
                      {item.is_current ? (
                        <span className="text-xs uppercase tracking-wide text-sky-400">current</span>
                      ) : null}
                    </div>
                    <p className="mt-1 text-sm text-slate-400">{item.server || item.cluster || "cluster"}</p>
                    <p className="text-xs text-slate-500">namespace: {item.namespace || "default"}</p>
                  </button>
                </li>
              );
            })
          )}
        </ul>
      </section>

      {error ? <p className="mt-4 whitespace-pre-wrap text-sm text-rose-400">{error}</p> : null}

      <section className="mt-10">
        <h2 className="text-lg font-medium">Investigation Status</h2>
        {investigating ? (
          <p className="mt-2 text-sky-300">Investigating Kubernetes Cluster...</p>
        ) : null}
        <ul className="mt-3 space-y-2 text-slate-300">
          {steps
            .filter((step) => step.key !== "done")
            .map((step) => (
              <li key={step.key}>
                {step.done ? "✓" : investigating && active?.current_step === step.key ? "…" : "○"} {step.label}
              </li>
            ))}
        </ul>
      </section>

      {active?.status === "error" && active.message ? (
        <p className="mt-6 whitespace-pre-wrap text-sm text-amber-300">{active.message}</p>
      ) : null}

      {healthy ? (
        <section className="mt-10 rounded-2xl border border-emerald-800 bg-emerald-950/40 p-5">
          <h2 className="text-lg font-medium text-emerald-200">Cluster Health</h2>
          <p className="mt-3 whitespace-pre-wrap text-slate-200">{CLUSTER_HEALTHY}</p>
        </section>
      ) : null}

      {diagnosisReady ? (
        <section className="mt-10 rounded-2xl border border-slate-800 bg-slate-900/60 p-5">
          <h2 className="text-lg font-medium">Diagnosis</h2>
          {active.cluster ? <p className="mt-2 text-sm text-slate-500">Cluster: {active.cluster}</p> : null}
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
                <span>
                  {item.cluster ? <span className="mr-2 text-slate-500">{item.cluster}</span> : null}
                  {item.root_cause || item.status}
                </span>
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
