import axios from "axios";

export function friendlyApiError(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const data = error.response?.data as { message?: string } | undefined;
    const message = (data?.message || "").trim();
    if (message && !/traceback/i.test(message)) {
      return message;
    }
    if (error.code === "ECONNABORTED") {
      return "The investigation timed out.\n\nPlease retry. If this continues, check cluster connectivity and OpenRouter.";
    }
    if (error.response?.status === 401) {
      return "Please sign in again.\n\nYour session is missing or expired.";
    }
    if (!error.response) {
      return "Cannot reach the investigation API.\n\nIs the backend running? Check NEXT_PUBLIC_API_BASE_URL.";
    }
    return "The investigation request failed.\n\nPlease retry. If this continues, check kubeconfig and backend logs.";
  }
  if (error instanceof Error && error.message && !/traceback/i.test(error.message)) {
    return error.message;
  }
  return "Something went wrong. Please retry.";
}

export function friendlyAuthError(message: string): string {
  const lowered = message.toLowerCase();
  if (lowered.includes("invalid login")) {
    return "Email or password is incorrect.";
  }
  if (lowered.includes("email not confirmed")) {
    return "Confirm your email in Supabase Auth, or disable Confirm email for local demos.";
  }
  if (lowered.includes("user already registered")) {
    return "That email already has an account. Sign in instead.";
  }
  return message;
}

export const CLUSTER_HEALTHY =
  "No critical Kubernetes issues detected. Cluster appears healthy.";
