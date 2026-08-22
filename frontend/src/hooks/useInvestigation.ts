import { useQuery, useMutation } from '@tanstack/react-query';
import { investigationService, InvestigationRequest } from '@/services/investigationService';

export const useHealth = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: () => investigationService.getHealth(),
    refetchInterval: 30000, // Refetch every 30 seconds
  });
};

export const useStatus = () => {
  return useQuery({
    queryKey: ['status'],
    queryFn: () => investigationService.getStatus(),
    refetchInterval: 30000,
  });
};

export const useInvestigate = () => {
  return useMutation({
    mutationFn: (request: InvestigationRequest) =>
      investigationService.startInvestigation(request),
  });
};
