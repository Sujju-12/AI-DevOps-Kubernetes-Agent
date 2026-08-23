/** @type {import('next').NextConfig} */
const supabaseUrl =
  process.env.NEXT_PUBLIC_SUPABASE_URL || "https://tzdxvhbdpkqckkmecytz.supabase.co";
// Publishable anon key for this app's Supabase project (safe to ship; RLS still applies).
const supabaseAnonKey =
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InR6ZHh2aGJkcGtxY2trbWVjeXR6Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc0NTk4NzUsImV4cCI6MjEwMzAzNTg3NX0.l45EW90Z7QhEdGZfLTiTwUdcyyYY0YCv9UK0iQRYtsY";

const nextConfig = {
  output: "standalone",
  env: {
    NEXT_PUBLIC_API_BASE_URL: process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000",
    NEXT_PUBLIC_SUPABASE_URL: supabaseUrl,
    NEXT_PUBLIC_SUPABASE_ANON_KEY: supabaseAnonKey,
    NEXT_PUBLIC_SUPABASE_PROJECT_REF:
      process.env.NEXT_PUBLIC_SUPABASE_PROJECT_REF || "tzdxvhbdpkqckkmecytz",
  },
};

module.exports = nextConfig;
