"use client";

import type { Diagnosis } from "@/types";

export function DiagnosisCard({ diagnosis }: { diagnosis: Diagnosis }) {
  return (
    <section className="rounded-2xl border border-slate-800 bg-slate-900/70 p-6">
      <div className="mb-4 flex items-center justify-between gap-4">
        <h2 className="text-lg font-semibold">Diagnosis</h2>
        <span className="rounded-full bg-emerald-500/15 px-3 py-1 text-sm text-emerald-300">
          Confidence {diagnosis.confidence}%
        </span>
      </div>
      <dl className="space-y-4 text-sm">
        <div>
          <dt className="text-slate-400">Root Cause</dt>
          <dd className="mt-1 text-base text-white">{diagnosis.root_cause}</dd>
        </div>
        <div>
          <dt className="text-slate-400">Explanation</dt>
          <dd className="mt-1 text-slate-200">{diagnosis.explanation}</dd>
        </div>
        <div>
          <dt className="text-slate-400">Suggested Fix</dt>
          <dd className="mt-1 text-slate-200">{diagnosis.fix}</dd>
        </div>
        <div>
          <dt className="text-slate-400">kubectl Command</dt>
          <dd className="mt-1 overflow-x-auto rounded-lg bg-black/40 p-3 font-mono text-xs text-sky-200">
            {diagnosis.kubectl_command}
          </dd>
        </div>
        {diagnosis.prevention ? (
          <div>
            <dt className="text-slate-400">Prevention</dt>
            <dd className="mt-1 text-slate-200">{diagnosis.prevention}</dd>
          </div>
        ) : null}
        <p className="text-xs text-slate-500">Engine: {diagnosis.engine} (local)</p>
      </dl>
    </section>
  );
}
