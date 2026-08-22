"use client";

import type { InvestigationRecord } from "@/types";

export function HistoryTable({ items }: { items: InvestigationRecord[] }) {
  if (!items.length) {
    return <p className="text-sm text-slate-500">No previous investigations yet.</p>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-left text-sm">
        <thead className="text-slate-400">
          <tr>
            <th className="pb-2 font-medium">Time</th>
            <th className="pb-2 font-medium">Cluster</th>
            <th className="pb-2 font-medium">Root Cause</th>
            <th className="pb-2 font-medium">Confidence</th>
            <th className="pb-2 font-medium">Status</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.id} className="border-t border-slate-800">
              <td className="py-2 text-slate-300">{new Date(item.timestamp).toLocaleString()}</td>
              <td className="py-2 text-slate-300">{item.context || "—"}</td>
              <td className="py-2 text-slate-100">{item.root_cause}</td>
              <td className="py-2 text-slate-300">{item.confidence}%</td>
              <td className="py-2 text-slate-300">{item.status}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
