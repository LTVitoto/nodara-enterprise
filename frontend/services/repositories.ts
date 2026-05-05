const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function fetchAPI(end: string, opts?: RequestInit) {
  const res = await fetch(`${API}${end}`, {
    ...opts, headers: { "Content-Type": "application/json", ...opts?.headers }
  });
  if(!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}
function norm(d: any) { return Array.isArray(d) ? d : (d?.data || d?.items || []); }

export const projectsRepository = {
  list: async () => norm(await fetchAPI("/api/projects")),
  get: async (id: string) => await fetchAPI(`/api/projects/${id}`),
  create: async (p: any) => await fetchAPI("/api/projects", { method: "POST", body: JSON.stringify(p) }),
  patch: async (id: string, p: any) => await fetchAPI(`/api/projects/${id}`, { method: "PATCH", body: JSON.stringify(p) })
};

export const futureRepository = {
  messages: async (id: string) => norm(await fetchAPI(`/api/projects/${id}/messages`)),
  workspace: async (id: string) => norm(await fetchAPI(`/api/projects/${id}/workspace/tree`)),
  workspaceFile: async (id: string, path: string) => await fetchAPI(`/api/projects/${id}/workspace/file?file_path=${encodeURIComponent(path)}`),
  readme: async (id: string) => await fetchAPI(`/api/projects/${id}/readme`),
  updateReadme: async (id: string, c: string) => await fetchAPI(`/api/projects/${id}/readme`, { method: "PATCH", body: JSON.stringify({ content: c }) }),
  metrics: async () => norm(await fetchAPI("/api/metrics")),
  agents: async () => norm(await fetchAPI("/api/agents")),
  tools: async () => norm(await fetchAPI("/api/tools")),
  audit: async () => norm(await fetchAPI("/api/audit/events"))
};

export const githubRepository = {
  status: async (id: string) => await fetchAPI(`/api/github/${id}/status`, { method: "POST" }),
  add: async (id: string) => await fetchAPI(`/api/github/${id}/add`, { method: "POST" }),
  commit: async (id: string) => await fetchAPI(`/api/github/${id}/commit`, { method: "POST" }),
  push: async (id: string) => await fetchAPI(`/api/github/${id}/push`, { method: "POST" })
};

export const filesRepository = {
  list: async (id: string) => norm(await fetchAPI(`/api/files/${id}`)),
  upload: async (id: string, file: File) => {
    const data = new FormData();
    data.append("file", file);
    const res = await fetch(`${API}/api/files/${id}/upload`, { method: "POST", body: data });
    return await res.json();
  }
};

export const configRepository = {
  list: async () => norm(await fetchAPI("/api/config")),
  patch: async (id: number, p: any) => await fetchAPI(`/api/config/${id}`, { method: "PATCH", body: JSON.stringify(p) })
};

export const approvalsRepository = {
  listAll: async () => norm(await fetchAPI("/api/approvals")),
  approve: async (id: number) => await fetchAPI(`/api/approvals/${id}/approve`, { method: "POST" }),
  reject: async (id: number) => await fetchAPI(`/api/approvals/${id}/reject`, { method: "POST" })
};
