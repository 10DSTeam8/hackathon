// src/api/hooks.ts  (DROP-IN REPLACEMENT)

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { http } from "./client";
import type {
  DaySummary,
  AppointmentSummary,
  Appointment,
  Strategy,
  Deployment,
  LogEntry,
  SimStatus,
  TickResult,
} from "./types";

export const keys = {
  day: (date: string) => ["day", date] as const,
  appointments: (date: string) => ["appointments", date] as const,
  appointment: (id?: string) => ["appointment", id] as const,
  strategies: ["strategies"] as const,
  logs: (date: string) => ["logs", date] as const,
  health: ["health"] as const,
  simStatus: ["simStatus"] as const,
};

export function useHealth() {
  return useQuery({
    queryKey: keys.health,
    queryFn: () => http.get<{ ok: boolean; todayIndex: number; startDateISO: string; todayDateISO: string }>("/health"),
  });
}

export function useDaySummary(dateISO: string) {
  return useQuery({
    queryKey: keys.day(dateISO),
    queryFn: () => http.get<DaySummary>(`/day/summary?date=${dateISO}`),
    staleTime: 2_000,
  });
}

export function useAppointments(dateISO: string) {
  return useQuery({
    queryKey: keys.appointments(dateISO),
    queryFn: () => http.get<AppointmentSummary[]>(`/appointments?date=${dateISO}`),
    staleTime: 2_000,
  });
}

export function useAppointment(id?: string) {
  return useQuery({
    enabled: !!id,
    queryKey: keys.appointment(id),
    queryFn: () => http.get<Appointment>(`/appointments/${id}`),
  });
}

export function useStrategies() {
  return useQuery({ queryKey: keys.strategies, queryFn: () => http.get<Strategy[]>("/strategies") });
}

export function useLogs(dateISO: string) {
  return useQuery({
    queryKey: keys.logs(dateISO),
    queryFn: () => http.get<LogEntry[]>(`/logs?date=${dateISO}`),
    refetchInterval: 3000,
  });
}

export function useSimStatus() {
  return useQuery({
    queryKey: keys.simStatus,
    queryFn: () => http.get<SimStatus>("/simulate/status"),
    refetchInterval: 2000,
  });
}

// >>> CHANGED: no args; always +1 day on server
export function useAdvanceDay() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () =>
      http.post<{ ok: true; todayIndex: number; todayDateISO: string }>(`/simulate/advance`),
    onSuccess: () => {
      qc.invalidateQueries(); // refresh all state
    },
  });
}

export function useTickToday() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => http.post<TickResult>("/simulate/tick_today"),
    onSuccess: () => {
      qc.invalidateQueries();
    },
  });
}

export function useSendSMS() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { appointment_id: string; template: string }) =>
      http.post<{ ok: true }>("/actions/send_sms", vars),
    onSuccess: () => qc.invalidateQueries(),
  });
}

export function useCallNow() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (appointment_id: string) =>
      http.post<{ ok: true }>("/actions/call_now", { appointment_id }),
    onSuccess: () => qc.invalidateQueries(),
  });
}

export function useCreateStrategy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: Omit<Strategy, "id">) => http.post<Strategy>("/strategies", payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.strategies }),
  });
}

export function usePatchStrategy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (vars: { id: string; payload: Partial<Strategy> }) =>
      http.patch<Strategy>(`/strategies/${vars.id}`, vars.payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: keys.strategies }),
  });
}

export function useDeploy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (payload: { target_date: string; strategy_ids: string[] }) =>
      http.post<Deployment>("/deploy", payload),
    onSuccess: () => qc.invalidateQueries(),
  });
}