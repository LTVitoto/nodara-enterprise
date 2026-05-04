const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/* =========================
   SAFE FETCH
========================= */
async function safeFetch(url: string, options?: RequestInit) {
  try {
    const res = await fetch(url, {
      cache: "no-store",
      ...options
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);

    return await res.json();
  } catch (err) {
    console.error("API ERROR:", err);
    return null;
  }
}

/* =========================
   APPROVALS
========================= */
export async function getApprovals(status?: string) {
  const url = status && status !== "all"
    ? `${API_URL}/api/approvals?status=${status}`
    : `${API_URL}/api/approvals`;

  const data = await safeFetch(url);
  return Array.isArray(data) ? data : [];
}

export async function approveApproval(id: number) {
  return safeFetch(`${API_URL}/api/approvals/${id}/approve`, {
    method: "POST"
  });
}

export async function rejectApproval(id: number) {
  return safeFetch(`${API_URL}/api/approvals/${id}/reject`, {
    method: "POST"
  });
}