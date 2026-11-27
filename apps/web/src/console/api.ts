export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

export type Account = { user_id: string; nickname: string; email: string };

export type SkillSummary = {
  name: string;
  display_name: string;
  description: string;
  category_id: string;
  category_label: string;
  visibility: "public" | "private";
  current_content_hash: string;
  version: string;
  dirty: boolean;
  updated_at: string;
};

export type SkillFile = {
  path: string;
  sha256: string;
  size: number;
  content?: string;
  binary?: boolean;
};

export type SkillChange = { path: string; status: "added" | "removed" | "modified" };

export type SkillDetail = { skill: SkillSummary; files: SkillFile[]; changes: SkillChange[] };

export type SkillVersion = {
  content_hash: string;
  version: string;
  changelog: string;
  published_at: string;
};

type Envelope<T> = { success: boolean; message: string; data: T };

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, { ...init, credentials: "same-origin" });
  const payload = (await response.json()) as Envelope<T>;
  if (!response.ok || !payload.success) throw new ApiError(payload.message || "请求失败", response.status);
  return payload.data;
}

export function fetchSession(): Promise<Account> {
  return request("/api/accounts/session");
}

export function registerAccount(userId: string, nickname: string, password: string): Promise<Account> {
  return request("/api/accounts/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, nickname, password }),
  });
}

export function loginAccount(userId: string, password: string): Promise<Account> {
  return request("/api/accounts/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id: userId, password }),
  });
}

export function logoutAccount(): Promise<Record<string, never>> {
  return request("/api/accounts/logout", { method: "POST" });
}

export function fetchSkills(): Promise<{ skills: SkillSummary[] }> {
  return request("/api/skills");
}

export function fetchSkill(name: string, token = ""): Promise<SkillDetail> {
  return request(`/api/skills/${name}`, token ? { headers: { Authorization: `Bearer ${token}` } } : undefined);
}

export function updateSkill(name: string, input: { display_name: string; description: string; category: string; visibility: string }): Promise<SkillDetail> {
  return request(`/api/skills/${name}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function deleteSkill(name: string): Promise<Record<string, never>> {
  return request(`/api/skills/${name}`, { method: "DELETE" });
}

export function createSkill(input: { name: string; display_name: string; description: string; visibility: string; file?: File }): Promise<SkillDetail> {
  if (input.file) {
    const body = new FormData();
    body.set("name", input.name);
    body.set("display_name", input.display_name);
    body.set("description", input.description);
    body.set("visibility", input.visibility);
    body.set("file", input.file);
    return request("/api/skills", { method: "POST", body });
  }
  return request("/api/skills", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}

export function saveDraft(name: string, files: SkillFile[]): Promise<SkillDetail> {
  return request(`/api/skills/${name}/draft`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      files: files.map((file) => (file.binary ? { path: file.path, binary: true } : { path: file.path, content: file.content ?? "" })),
    }),
  });
}

export function uploadZip(name: string, file: File): Promise<SkillDetail> {
  const body = new FormData();
  body.set("file", file);
  return request(`/api/skills/${name}/upload`, { method: "POST", body });
}

export function publishSkill(name: string, changelog: string): Promise<SkillVersion> {
  return request(`/api/skills/${name}/publish`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ changelog }),
  });
}

export function fetchVersions(name: string): Promise<{ versions: SkillVersion[] }> {
  return request(`/api/skills/${name}/versions`);
}

export function rollbackSkill(name: string, contentHash: string): Promise<SkillDetail> {
  return request(`/api/skills/${name}/rollback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content_hash: contentHash }),
  });
}

export function fetchToken(): Promise<{ token: string }> {
  return request("/api/token");
}

export function resetToken(): Promise<{ token: string }> {
  return request("/api/token/reset", { method: "POST" });
}

export type PublicManifest = {
  name: string;
  version: string;
  display_name?: string;
  description?: string;
  category_id?: string;
  category_label?: string;
  files: { path: string; sha256: string; size: number }[];
};

export async function fetchManifest(userId: string, name: string, token = ""): Promise<PublicManifest> {
  const url = new URL(`/${userId}/skills/${name}/manifest.json`, window.location.origin);
  if (token) url.searchParams.set("token", token);
  const response = await fetch(url, { credentials: "same-origin" });
  if (!response.ok) throw new ApiError("不存在", response.status);
  return (await response.json()) as PublicManifest;
}
