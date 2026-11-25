import { useEffect, useState } from "react";
import { fetchSession, type Account } from "@/console/api";

export type SessionState = {
  status: "loading" | "guest" | "in";
  account: Account | null;
};

let cached: SessionState | null = null;
let pending: Promise<SessionState> | null = null;

export function loadSession(): Promise<SessionState> {
  if (cached) return Promise.resolve(cached);
  if (!pending) {
    pending = fetchSession()
      .then((account) => {
        cached = { status: "in", account };
        return cached;
      })
      .catch(() => {
        cached = { status: "guest", account: null };
        return cached;
      });
  }
  return pending;
}

export function useSession(): SessionState {
  const [session, setSession] = useState<SessionState>(cached ?? { status: "loading", account: null });
  useEffect(() => {
    let alive = true;
    void loadSession().then((next) => {
      if (alive) setSession(next);
    });
    return () => {
      alive = false;
    };
  }, []);
  return session;
}

export function accountHomeHref(session: SessionState) {
  return session.status === "in" && session.account ? `/${session.account.user_id}` : "/login";
}

export function followAccountHome(event: { preventDefault(): void }, session: SessionState) {
  if (session.status !== "loading") return;
  event.preventDefault();
  void loadSession().then((next) => {
    window.location.assign(accountHomeHref(next));
  });
}
