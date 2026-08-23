"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { ClusterPicker } from "@/components/ClusterPicker";
import { DiagnosisCard } from "@/components/DiagnosisCard";
import { HistoryTable } from "@/components/HistoryTable";
import { ProgressList } from "@/components/ProgressList";
import { useClusters, useHealth, useHistory, useInvestigate } from "@/hooks/useInvestigation";
import { loadToken, setToken } from "@/services/api";
import type { Diagnosis, InvestigationRecord } from "@/types";

const STEP_DEFS = [
  { key: "pods", label: "Checking Pods" },
  { key: "logs", label: "Reading Logs" },
  { key: "events", label: "Analyzing Events" },
  { key: "deployments", label: "Inspecting Deployments" },
  { key: "network", label: "Checking Networking" },
  { key: "ai", label: "AI Reasoning" },
  { key: "done", label: "Root Cause Found" },
];

export default function HomePage() {
  const router = useRouter();
  const [ready, setReady] = useState(false);
  const [selected, setSelected] = useState<string>();
  const [doneSteps, setDoneSteps] = useState<string[]>([]);
  const [diagnosis, setDiagnosis] = useState<Diagnosis | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [investigating, setInvestigating] = useState(false);
  const [localHistory, setLocalHistory] = useState<InvestigationRecord[]>([]);

  const health = useHealth();
  const clusters = useClusters(ready);
  const history = useHistory(ready);
  const mutation = useInvestigate();

  useEffect(() => {
    if (!loadToken()) {
      router.replace("/login");
      return;
    }
    setReady(true);
  }, [router]);

  useEffect(() => {
    if (!selected && clusters.data?.contexts?.length) {
      const current = clusters.data.contexts.find((item) => item.is_current) || clusters.data.contexts[0];
      setSelected(current.name);
    }
  }, [clusters.data, selected]);

  const steps = useMemo(
    () => STEP_DEFS.map((step) => ({ ...step, done: doneSteps.includes(step.key), active: investigating && !doneSteps.length })),
    [doneSteps, investigating]
  );

  async function runInvestigation() {
    setInvestigating(true);
    setError(null);
    setDiagnosis(null);
    setDoneSteps([]);
    try {
      const result = await mutation.mutateAsync(selected);
      setDoneSteps(STEP_DEFS.map((step) => step.key));
      if (result.status === "error") setError(result.error || result.diagnosis?.explanation || "Investigation failed");
      if (result.diagnosis) setDiagnosis(result.diagnosis);
      if (result.history) setLocalHistory(result.history);
      await history.refetch();
    } catch {
      setError("Unable to reach the local backend. Confirm it is running on port 8000.");
    } finally {
      setInvestigating(false);
    }
  }

  if (!ready) return null;

  const records = localHistory.length ? localHistory : history.data || [];
  const healthy = diagnosis && diagnosis.root_cause.toLowerCase().includes("no critical kubernetes issues");

  return (
    <main className="mx-auto min-h-screen max-w-5xl px-6 py-10">
      <header className="mb-8 flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-semibold">AI Kubernetes Agent</h1>
          <p className="mt-1 text-slate-400">Troubleshoot Kubernetes with AI</p>
        </div>
        <div className="flex items-center gap-3 text-sm">
          <span className="rounded-full bg-slate-800 px-3 py-1 text-slate-300">
            System Status: {health.data?.status === "healthy" ? "Ready" : "Checking"}
          </span>
          <button className="text-slate-400 underline" onClick={() => { setToken(null); router.push("/login"); }}>
            Sign out
          </button>
        </div>
      </header>

      <div className="space-y-8">
        <ClusterPicker contexts={clusters.data?.contexts || []} selected={selected} onSelect={setSelected} warning={clusters.data?.warning} />
        <div>
          <button onClick={runInvestigation} disabled={investigating} className="rounded-xl bg-sky-500 px-6 py-3 font-semibold text-slate-950 disabled:opacity-60">
            {investigating ? "Investigating Kubernetes Cluster..." : "Investigate Cluster"}
          </button>
          {selected ? <p className="mt-2 text-sm text-slate-400">Selected context: {selected}</p> : null}
        </div>
        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
          <h2 className="mb-4 text-lg font-semibold">Investigation Status</h2>
          {investigating ? <p className="mb-4 text-sm text-sky-300">Investigating Kubernetes Cluster...</p> : null}
          <ProgressList steps={steps} />
        </section>
        {error ? <p className="whitespace-pre-wrap rounded-xl border border-rose-500/30 bg-rose-500/10 p-4 text-sm text-rose-100">{error}</p> : null}
        {healthy ? (
          <p className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-4 text-sm text-emerald-100">
            No critical Kubernetes issues detected. Cluster appears healthy.
          </p>
        ) : null}
        {diagnosis && !healthy ? <DiagnosisCard diagnosis={diagnosis} /> : null}
        <section className="rounded-2xl border border-slate-800 bg-slate-900/50 p-6">
          <h2 className="mb-4 text-lg font-semibold">Previous Investigations</h2>
          <HistoryTable items={records} />
        </section>
      </div>
    </main>
  );
}
