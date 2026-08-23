"use client";

import { useState } from "react";
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
      setError(authError.message);
    }
  }

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6">
      <h1 className="text-3xl font-semibold tracking-tight">AI Kubernetes Agent</h1>
      <p className="mt-2 text-slate-400">Sign in to investigate your cluster.</p>
      <form onSubmit={onSubmit} className="mt-8 space-y-4">
        <input
          className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          type="email"
          placeholder="Email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
        <input
          className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2"
          type="password"
          placeholder="Password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          required
          minLength={6}
        />
        {error ? <p className="text-sm text-rose-400">{error}</p> : null}
        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-xl bg-sky-500 px-6 py-3 font-semibold text-slate-950 disabled:opacity-60"
        >
          {busy ? "Please wait..." : mode === "signin" ? "Sign in" : "Create account"}
        </button>
      </form>
      <button
        type="button"
        className="mt-4 text-sm text-sky-400"
        onClick={() => setMode(mode === "signin" ? "signup" : "signin")}
      >
        {mode === "signin" ? "Need an account? Sign up" : "Have an account? Sign in"}
      </button>
    </main>
  );
}
