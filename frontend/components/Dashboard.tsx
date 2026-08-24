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
  const healthLabel = health.isLoading ? "Checking" : ready ? "Ready" : "Unavailable";

  return (
    <main className="relative mx-auto min-h-screen max-w-4xl px-4 py-10 sm:px-6">
      <div className="k8s-grid pointer-events-none absolute inset-0 opacity-40" />
      <div className="relative">
        <header className="flex items-start justify-between gap-4 border-b border-slate-800/80 pb-6">
          <div>
            <p className="mb-2 text-[11px] font-medium uppercase tracking-[0.2em] text-cyan-300/80">Operations</p>
            <h1 className="text-3xl font-semibold tracking-tight text-white">AI Kubernetes Agent</h1>
            <p className="mt-2 flex items-center gap-2 text-sm text-slate-400">
              <span
                className={`status-dot ${ready ? "bg-emerald-400" : health.isLoading ? "bg-cyan-400 pulse-soft" : "bg-amber-400"}`}
              />
              System Status: {healthLabel}
            </p>
          </div>
          <button
            type="button"
            className="rounded-full border border-slate-700 bg-slate-950/60 px-3 py-1.5 text-sm text-slate-300 transition hover:border-cyan-400/40 hover:text-white"
            onClick={() => supabase.auth.signOut()}
          >
            Sign out
          </button>
        </header>

        <section className="mt-8">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <h2 className="text-lg font-medium text-white">Kubernetes Clusters</h2>
            <input
              className="w-56 rounded-xl border border-slate-700/80 bg-slate-950/70 px-3 py-2 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-400/50 focus:ring-4 focus:ring-cyan-400/10"
              placeholder="Namespace (optional)"
              value={namespace}
              onChange={(event) => setNamespace(event.target.value)}
            />
          </div>
          <p className="mt-1 text-sm text-slate-500">
            Click a cluster from your kubeconfig to investigate it.
          </p>
          {clustersMessage ? (
            <p className="mt-3 whitespace-pre-wrap rounded-xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
              {clustersMessage}
            </p>
          ) : null}
          <ul className="mt-4 grid gap-3">
            {clusters.length === 0 && !clustersMessage ? (
              <li className="glass-panel rounded-xl px-4 py-5 text-slate-500">No clusters found in kubeconfig.</li>
            ) : (
              clusters.map((item) => {
                const selected = selectedContext === item.name;
                return (
                  <li key={item.name}>
                    <button
                      type="button"
                      disabled={busy}
                      onClick={() => investigateContext(item.name)}
                      className={`cluster-card w-full rounded-2xl px-4 py-4 text-left ${
                        selected ? "border-cyan-400/50 shadow-[0_0_0_1px_rgba(34,211,238,0.25)]" : ""
                      }`}
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="font-medium text-white">{item.name}</span>
                        {item.is_current ? (
                          <span className="rounded-full border border-cyan-400/30 bg-cyan-400/10 px-2 py-0.5 text-xs uppercase tracking-wide text-cyan-300">
                            current
                          </span>
                        ) : null}
                      </div>
                      <p className="mt-1 text-sm text-slate-400">{item.server || item.cluster || "cluster"}</p>
                      <p className="font-mono text-xs text-slate-500">namespace: {item.namespace || "default"}</p>
                    </button>
                  </li>
                );
              })
            )}
          </ul>
        </section>

        {error ? (
          <p className="mt-4 whitespace-pre-wrap rounded-xl border border-rose-400/25 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
            {error}
          </p>
        ) : null}

        <section className="glass-panel mt-10 rounded-2xl p-5">
          <h2 className="text-lg font-medium text-white">Investigation Status</h2>
          {investigating ? (
            <p className="mt-2 flex items-center gap-2 text-cyan-300">
              <span className="status-dot bg-cyan-400 pulse-soft" />
              Investigating Kubernetes Cluster...
            </p>
          ) : null}
          <ul className="mt-3 space-y-2 text-slate-300">
            {steps
              .filter((step) => step.key !== "done")
              .map((step) => {
                const current = investigating && active?.current_step === step.key;
                return (
                  <li
                    key={step.key}
                    className={`flex items-center gap-3 rounded-lg px-3 py-2 text-sm ${
                      step.done
                        ? "bg-emerald-500/10 text-emerald-100"
                        : current
                          ? "bg-cyan-500/10 text-cyan-100"
                          : "bg-slate-950/40"
                    }`}
                  >
                    <span className="w-4 font-mono text-xs">
                      {step.done ? "✓" : current ? "…" : "○"}
                    </span>
                    {step.label}
                  </li>
                );
              })}
          </ul>
        </section>

        {active?.status === "error" && active.message ? (
          <p className="mt-6 whitespace-pre-wrap rounded-xl border border-amber-400/20 bg-amber-400/10 px-4 py-3 text-sm text-amber-100">
            {active.message}
          </p>
        ) : null}

        {healthy ? (
          <section className="mt-10 rounded-2xl border border-emerald-400/25 bg-emerald-950/50 p-5 shadow-[0_12px_40px_rgba(16,185,129,0.08)]">
            <h2 className="text-lg font-medium text-emerald-200">Cluster Health</h2>
            <p className="mt-3 whitespace-pre-wrap text-slate-200">{CLUSTER_HEALTHY}</p>
          </section>
        ) : null}

        {diagnosisReady ? (
          <section className="glass-panel mt-10 rounded-2xl p-5">
            <h2 className="text-lg font-medium text-white">Diagnosis</h2>
            {active.cluster ? <p className="mt-2 text-sm text-slate-500">Cluster: {active.cluster}</p> : null}
            <p className="mt-4 text-xs font-medium uppercase tracking-[0.16em] text-cyan-300/80">Root Cause</p>
            <p className="mt-1 text-lg text-white">{active.root_cause}</p>
            <p className="mt-4 text-xs font-medium uppercase tracking-[0.16em] text-slate-500">Explanation</p>
            <p className="mt-1 text-slate-300">{active.explanation}</p>
            <p className="mt-4 text-xs font-medium uppercase tracking-[0.16em] text-slate-500">Suggested Fix</p>
            <p className="mt-1 text-slate-300">{active.fix}</p>
            <p className="mt-4 text-xs font-medium uppercase tracking-[0.16em] text-slate-500">Command</p>
            <pre className="mt-1 overflow-x-auto rounded-xl border border-slate-800 bg-slate-950 p-3 font-mono text-sm text-cyan-300">
              {active.kubectl_command}
            </pre>
            <p className="mt-4 text-slate-300">
              Confidence: <span className="font-semibold text-white">{active.confidence}%</span>
            </p>
          </section>
        ) : null}

        <section className="mt-10">
          <h2 className="text-lg font-medium text-white">Recent Investigations</h2>
          <ul className="mt-3 space-y-2 text-slate-300">
            {history.length === 0 ? (
              <li className="text-slate-500">No investigations yet.</li>
            ) : (
              history.map((item) => (
                <li
                  key={item.id}
                  className="flex justify-between gap-3 rounded-xl border border-slate-800/90 bg-slate-950/40 px-4 py-3"
                >
                  <span>
                    {item.cluster ? <span className="mr-2 text-slate-500">{item.cluster}</span> : null}
                    {item.root_cause || item.status}
                  </span>
                  <span className="shrink-0 text-sm text-slate-500">
                    {item.confidence ? `${item.confidence}%` : item.status}
                  </span>
                </li>
              ))
            )}
          </ul>
        </section>
      </div>
    </main>
  );
}
