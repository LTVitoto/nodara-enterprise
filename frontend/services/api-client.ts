import { API_BASE_URL, DATA_MODE } from "@/lib/env";

export class ApiError extends Error {
  status: number;
  body: string;

  constructor(message: string, status: number, body: string) {
    super(message);
    this.status = status;
    this.body = body;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  const response = await fetch(url, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(init?.headers || {})
    },
    cache: "no-store"
  });

  const raw = await response.text();
  if (!response.ok) {
    throw new ApiError(`HTTP ${response.status} al consumir ${path}`, response.status, raw);
  }

  if (!raw) return undefined as T;
  return JSON.parse(raw) as T;
}

export function shouldUseMock() {
  return DATA_MODE === "mock";
}

export function shouldFallbackToMock() {
  return DATA_MODE === "hybrid";
}

export async function withMockFallback<T>(realCall: () => Promise<T>, mockCall: () => T | Promise<T>): Promise<T> {
  if (shouldUseMock()) return mockCall();
  try {
    return await realCall();
  } catch (error) {
    if (shouldFallbackToMock()) return mockCall();
    throw error;
  }
}
