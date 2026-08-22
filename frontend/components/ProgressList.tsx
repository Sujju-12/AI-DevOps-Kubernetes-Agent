"use client";

type Props = {
  steps: { key: string; label: string; done: boolean; active: boolean }[];
};

export function ProgressList({ steps }: Props) {
  return (
    <ul className="space-y-2">
      {steps.map((step) => (
        <li key={step.key} className="flex items-center gap-3 text-sm">
          <span
            className={`flex h-6 w-6 items-center justify-center rounded-full text-xs ${
              step.done
                ? "bg-emerald-500/20 text-emerald-300"
                : step.active
                  ? "bg-sky-500/20 text-sky-300"
                  : "bg-slate-800 text-slate-500"
            }`}
          >
            {step.done ? "✓" : step.active ? "…" : "○"}
          </span>
          <span className={step.done || step.active ? "text-slate-100" : "text-slate-500"}>
            {step.label}
          </span>
        </li>
      ))}
    </ul>
  );
}
