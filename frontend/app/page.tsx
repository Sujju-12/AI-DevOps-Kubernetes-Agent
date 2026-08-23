"use client";

import { useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { Dashboard } from "@/components/Dashboard";
import { LoginForm } from "@/components/LoginForm";
import { getSupabase, isSupabaseConfigured } from "@/lib/supabase";

export default function HomePage() {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!isSupabaseConfigured()) {
      setReady(true);
      return;
    }
    const supabase = getSupabase();
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session);
      setReady(true);
    });
    const { data } = supabase.auth.onAuthStateChange((_event, next) => {
      setSession(next);
    });
    return () => data.subscription.unsubscribe();
  }, []);

  if (!ready) {
    return <main className="p-8 text-slate-400">Loading...</main>;
  }
  if (!isSupabaseConfigured()) {
    return (
      <main className="mx-auto max-w-md p-8">
        <h1 className="text-2xl font-semibold">AI Kubernetes Agent</h1>
        <p className="mt-4 text-slate-400">
          Supabase is not configured in this build. Copy <code>frontend/.env.example</code> to{" "}
          <code>frontend/.env.local</code>, then restart with <code>npm run dev</code> or{" "}
          <code>docker compose up --build</code>.
        </p>
      </main>
    );
  }
  if (!session) {
    return <LoginForm />;
  }
  return <Dashboard session={session} />;
}
