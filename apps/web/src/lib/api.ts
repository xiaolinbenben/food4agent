export type Envelope<T> = {
  success: boolean;
  message: string;
  data: T;
};

async function request<T>(path: string, init?: RequestInit): Promise<Envelope<T>> {
  const response = await fetch(path, init);
  const text = await response.text();
  if (!text) {
    throw new Error("服务未启动");
  }
  let payload: Envelope<T>;
  try {
    payload = JSON.parse(text) as Envelope<T>;
  } catch {
    throw new Error("服务未启动");
  }
  if (!response.ok || !payload.success) {
    throw new Error(payload.message || "请求失败");
  }
  return payload;
}

export function fetchHealth(): Promise<Envelope<{ status: string }>> {
  return request("/healthz");
}

export function fetchWoodfish(): Promise<Envelope<{ count: number }>> {
  return request("/api/woodfish");
}

export function knockWoodfish(): Promise<Envelope<{ count: number }>> {
  return request("/api/woodfish", { method: "POST" });
}
