"use client";

import { InvestigateButton } from "@/components/InvestigateButton";
import { useHealth } from "@/hooks/useHealth";

export default function HomePage() {
  const health = useHealth();
  const ready = health.data?.status === "healthy";

  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center px-6">
      <h1 className="text-4xl font-semibold tracking-tight">AI Kubernetes Agent</h1>
      <p className="mt-3 text-lg text-slate-400">Troubleshoot Kubernetes with AI</p>
      <div className="mt-10">
        <InvestigateButton />
      </div>
      <p className="mt-6 text-sm text-slate-400">
        System Status: {health.isLoading ? "Checking" : ready ? "Ready" : "Unavailable"}
      </p>
    </main>
  );
}
