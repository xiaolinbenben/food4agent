const skillSlug = /^[a-z0-9](?:[a-z0-9-]{0,30}[a-z0-9])?$/;
const reservedUserIDs = new Set([
  "skills", "registry", "console", "api", "docs", "assets", "static",
  "login", "settings", "admin", "mcp", "healthz", "skill",
]);

export type ConsoleRoute =
  | { kind: "login" }
  | { kind: "profile"; userId: string }
  | { kind: "token"; userId: string }
  | { kind: "list"; userId: string }
  | { kind: "new"; userId: string }
  | { kind: "detail"; userId: string; name: string; token: string }
  | { kind: "edit"; userId: string; name: string }
  | { kind: "versions"; userId: string; name: string }
  | { kind: "publish"; userId: string; name: string };

export function parseConsolePath(pathname: string): ConsoleRoute | null {
  if (pathname === "/login") return { kind: "login" };
  const parts = pathname.split("/").filter(Boolean);
  if (parts.length === 0) return null;
  const userId = parts[0].toLowerCase();
  if (!validUserID(userId) || reservedUserIDs.has(userId)) return null;
  if (parts.length === 1) return { kind: "profile", userId };
  if (parts.length === 2 && parts[1] === "token") return { kind: "token", userId };
  if (parts[1] !== "skills") return null;
  const rest = parts.slice(2);
  if (rest.length === 0) return { kind: "list", userId };
  if (rest.length === 1 && rest[0] === "new") return { kind: "new", userId };
  if (!skillSlug.test(rest[0]) || rest[0] === "new") return null;
  const name = rest[0];
  if (rest.length === 1) return { kind: "detail", userId, name, token: "" };
  if (rest.length === 3 && rest[1] === "g" && /^f4a_[A-Za-z0-9_-]{22}$/.test(rest[2])) {
    return { kind: "detail", userId, name, token: rest[2] };
  }
  if (rest.length === 2 && rest[1] === "edit") return { kind: "edit", userId, name };
  if (rest.length === 2 && rest[1] === "versions") return { kind: "versions", userId, name };
  if (rest.length === 3 && rest[1] === "releases" && rest[2] === "new") return { kind: "publish", userId, name };
  return null;
}

function validUserID(value: string) {
  return value.length >= 1 && value.length <= 39 && /^[a-z0-9](?:-?[a-z0-9])*$/.test(value);
}
