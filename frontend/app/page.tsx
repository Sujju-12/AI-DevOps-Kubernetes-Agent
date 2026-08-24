"use client";

import { useEffect, useState } from "react";
import type { Session } from "@supabase/supabase-js";
import { Dashboard } from "@/components/Dashboard";
import { LoginForm } from "@/components/LoginForm";
import { getSupabase } from "@/lib/supabase";

export default function HomePage() {
  const [session, setSession] = useState<Session | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
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
  if (!session) {
    return <LoginForm />;
  }
  return <Dashboard session={session} />;
}
