"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { fetchClusters, fetchHealth, fetchHistory, investigate } from "@/services/api";

export function useHealth() {
  return useQuery({ queryKey: ["health"], queryFn: fetchHealth });
}

export function useClusters(enabled: boolean) {
  return useQuery({ queryKey: ["clusters"], queryFn: fetchClusters, enabled });
}

export function useHistory(enabled: boolean) {
  return useQuery({ queryKey: ["history"], queryFn: fetchHistory, enabled });
}

export function useInvestigate() {
  return useMutation({ mutationFn: (context?: string) => investigate(context) });
}
