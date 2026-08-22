"use client";

import type { ClusterContext } from "@/types";

export function ClusterPicker({
  contexts,
  selected,
  onSelect,
  warning,
}: {
  contexts: ClusterContext[];
  selected?: string;
  onSelect: (name: string) => void;
  warning?: string | null;
}) {
  if (warning && contexts.length === 0) {
    return (
      <p className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-100">
        {warning}
      </p>
    );
  }

  return (
    <div>
      <h2 className="mb-3 text-sm font-medium uppercase tracking-wide text-slate-400">
        Local kubeconfig clusters
      </h2>
      <div className="grid gap-3 md:grid-cols-2">
        {contexts.map((ctx) => {
          const active = ctx.name === selected;
          return (
            <button
              key={ctx.name}
              type="button"
              onClick={() => onSelect(ctx.name)}
              className={`rounded-xl border p-4 text-left transition ${
                active
                  ? "border-sky-400 bg-sky-500/10"
                  : "border-slate-800 bg-slate-900/50 hover:border-slate-600"
              }`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-white">{ctx.name}</span>
                {ctx.is_current ? (
                  <span className="text-xs text-sky-300">current</span>
                ) : null}
              </div>
              <p className="mt-2 truncate text-xs text-slate-400">{ctx.server || ctx.cluster}</p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
