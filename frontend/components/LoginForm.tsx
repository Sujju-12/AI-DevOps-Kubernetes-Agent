"use client";

import { useState } from "react";
import { friendlyAuthError } from "@/lib/errors";
import { getSupabase } from "@/lib/supabase";

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [mode, setMode] = useState<"signin" | "signup">("signin");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError("");
    setBusy(true);
    const supabase = getSupabase();
    const action =
      mode === "signin"
        ? supabase.auth.signInWithPassword({ email, password })
        : supabase.auth.signUp({ email, password });
    const { error: authError } = await action;
    setBusy(false);
    if (authError) {
      setError(friendlyAuthError(authError.message));
    }
  }

  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-10">
      <div className="k8s-grid pointer-events-none absolute inset-0 opacity-70" />
      <div className="relative w-full max-w-md">
        <p className="mb-3 inline-flex items-center gap-2 rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 text-xs font-medium uppercase tracking-[0.18em] text-cyan-200">
          Local control plane
        </p>
        <h1 className="text-3xl font-semibold tracking-tight text-white">AI Kubernetes Agent</h1>
        <p className="mt-2 text-slate-400">Sign in to investigate your cluster.</p>
        <form onSubmit={onSubmit} className="glass-panel mt-8 space-y-4 rounded-2xl p-6 sm:p-7">
          <input
            className="w-full rounded-xl border border-slate-700/80 bg-slate-950/70 px-3 py-2.5 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-400/50 focus:ring-4 focus:ring-cyan-400/10"
            type="email"
            placeholder="Email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
          <input
            className="w-full rounded-xl border border-slate-700/80 bg-slate-950/70 px-3 py-2.5 text-sm text-slate-100 outline-none transition placeholder:text-slate-500 focus:border-cyan-400/50 focus:ring-4 focus:ring-cyan-400/10"
            type="password"
            placeholder="Password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            minLength={6}
          />
          {error ? (
            <p className="rounded-lg border border-rose-400/20 bg-rose-500/10 px-3 py-2 text-sm text-rose-100">{error}</p>
          ) : null}
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-xl bg-gradient-to-r from-cyan-400 to-indigo-400 px-6 py-3 font-semibold text-slate-950 shadow-[0_8px_24px_rgba(34,211,238,0.22)] transition hover:brightness-110 disabled:opacity-60"
          >
            {busy ? "Please wait..." : mode === "signin" ? "Sign in" : "Create account"}
          </button>
        </form>
        <button
          type="button"
          className="mt-4 text-sm text-cyan-300 underline decoration-cyan-800 underline-offset-4 hover:text-cyan-200"
          onClick={() => setMode(mode === "signin" ? "signup" : "signin")}
        >
          {mode === "signin" ? "Need an account? Sign up" : "Have an account? Sign in"}
        </button>
      </div>
    </main>
  );
}
