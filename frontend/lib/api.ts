export function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(new RegExp("(^| )" + name + "=([^;]+)"));
  return match ? decodeURIComponent(match[2]) : null;
}

export async function apiFetch(path: string, options: RequestInit = {}): Promise<Response> {
  const headers = new Headers(options.headers || {});
  const csrf = getCookie("lh_csrf");
  if (csrf && !headers.has("X-CSRF-Token")) {
    headers.set("X-CSRF-Token", csrf);
  }
  return fetch(path, {
    ...options,
    headers,
    credentials: "include",
  });
}

export function getAnalyticsConsent(): boolean {
  if (typeof window === "undefined") return true;
  const val = localStorage.getItem("lh_cookie_consent");
  return val !== "declined";
}

export async function trackEvent(
  type: "pageview" | "event",
  payload: { path?: string; event_name?: string; properties?: Record<string, any> }
) {
  try {
    if (typeof window === "undefined") return;
    let sessId = sessionStorage.getItem("lh_sess_id");
    if (!sessId) {
      sessId = Math.random().toString(36).slice(2) + Date.now().toString(36);
      sessionStorage.setItem("lh_sess_id", sessId);
    }
    const consent = getAnalyticsConsent();
    await apiFetch("/api/analytics/track", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        type,
        path: payload.path || window.location.pathname,
        event_name: payload.event_name,
        properties: payload.properties,
        session_id: consent ? sessId : null,
        referrer: document.referrer || null,
        consent_given: consent,
      }),
    });
  } catch {
    // Non-blocking analytics
  }
}
