import { ENABLED_SPRINTS } from "@/lib/env";
import type { Sprint } from "@/types/domain";

export const sprintLabels: Record<Sprint, string> = {
  1: "Sprint 1 · Operación base",
  2: "Sprint 2 · Contexto y tools",
  3: "Sprint 3 · Agentes y métricas",
  4: "Sprint 4 · GitHub y auditoría"
};

export function isSprintEnabled(sprint: Sprint) {
  return ENABLED_SPRINTS.includes(sprint);
}
