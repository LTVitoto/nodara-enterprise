import type { DataMode } from "@/types/domain";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
export const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_BASE_URL || "ws://localhost:8000";
export const DATA_MODE = (process.env.NEXT_PUBLIC_DATA_MODE || "hybrid") as DataMode;
export const DEFAULT_USER_CONFIG_ID = Number(process.env.NEXT_PUBLIC_DEFAULT_USER_CONFIG_ID || "1");
export const ENABLED_SPRINTS = (process.env.NEXT_PUBLIC_ENABLED_SPRINTS || "1,2,3,4")
  .split(",")
  .map((s) => Number(s.trim()))
  .filter(Boolean);

export function isMockMode() {
  return DATA_MODE === "mock";
}

export function isHybridMode() {
  return DATA_MODE === "hybrid";
}
