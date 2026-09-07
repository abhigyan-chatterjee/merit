export interface ApiErrorPayload {
  code: string;
  message: string;
}

export class ApiError extends Error {
  code: string;
  status: number;

  constructor(status: number, error: ApiErrorPayload) {
    super(error.message || `Request failed with status ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.code = error.code || "UNKNOWN_ERROR";
  }
}

export interface UserProfile {
  id: string;
  email: string;
  display_name: string;
  displayName: string;
  role: string;
  created_at: string;
  last_login_at: string | null;
}

function normalizeUser(raw: Record<string, unknown>): UserProfile {
  const data = (raw.user as Record<string, unknown>) || raw;
  const displayName = String(data.display_name || data.displayName || "");
  return {
    id: String(data.id || ""),
    email: String(data.email || ""),
    display_name: displayName,
    displayName,
    role: String(data.role || "student"),
    created_at: String(data.created_at || ""),
    last_login_at: data.last_login_at ? String(data.last_login_at) : null,
  };
}

let isRefreshing = false;
let refreshPromise: Promise<void> | null = null;

export async function apiRequest<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = endpoint;
  const headers = new Headers(options.headers || {});

  if (options.body && typeof options.body === "string" && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const fetchOptions: RequestInit = {
    ...options,
    headers,
    credentials: "include",
  };

  let response = await fetch(url, fetchOptions);

  // Handle 401 Unauthorized with token refresh (once)
  const isAuthEndpoint =
    endpoint.includes("/auth/login") ||
    endpoint.includes("/auth/register") ||
    endpoint.includes("/auth/refresh");

  if (response.status === 401 && !isAuthEndpoint) {
    if (!isRefreshing) {
      isRefreshing = true;
      refreshPromise = (async () => {
        try {
          const refRes = await fetch("/api/v1/auth/refresh", {
            method: "POST",
            credentials: "include",
          });
          if (!refRes.ok) {
            throw new Error("Refresh failed");
          }
        } finally {
          isRefreshing = false;
          refreshPromise = null;
        }
      })();
    }

    try {
      await refreshPromise;
      // Retry original request
      response = await fetch(url, fetchOptions);
    } catch {
      // Refresh failed, proceed to error handling
    }
  }

  if (!response.ok) {
    let errPayload: ApiErrorPayload = {
      code: `HTTP_${response.status}`,
      message: response.statusText,
    };
    try {
      const data = await response.json();
      if (data?.error) {
        errPayload = {
          code: data.error.code || errPayload.code,
          message: data.error.message || errPayload.message,
        };
      } else if (data?.detail) {
        if (typeof data.detail === "object") {
          errPayload = {
            code: data.detail.code || errPayload.code,
            message: data.detail.message || errPayload.message,
          };
        } else {
          errPayload.message = String(data.detail);
        }
      }
    } catch {
      // Non-JSON response
    }
    throw new ApiError(response.status, errPayload);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return (await response.json()) as T;
}

// Auth API Helpers
export const authApi = {
  async register(email: string, password: string, displayName: string): Promise<UserProfile> {
    const res = await apiRequest<Record<string, unknown>>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
        display_name: displayName,
      }),
    });
    return normalizeUser(res);
  },

  async login(email: string, password: string): Promise<UserProfile> {
    const res = await apiRequest<Record<string, unknown>>("/api/v1/auth/login", {
      method: "POST",
      body: JSON.stringify({
        email,
        password,
      }),
    });
    return normalizeUser(res);
  },

  async logout(): Promise<void> {
    await apiRequest<{ message: string }>("/api/v1/auth/logout", {
      method: "POST",
    });
  },

  async getMe(): Promise<UserProfile> {
    const res = await apiRequest<Record<string, unknown>>("/api/v1/auth/me", {
      method: "GET",
    });
    return normalizeUser(res);
  },

  async deleteAccount(): Promise<void> {
    await apiRequest<void>("/api/v1/auth/account", {
      method: "DELETE",
    });
  },

  async exportData(): Promise<Record<string, unknown>> {
    return await apiRequest<Record<string, unknown>>("/api/v1/auth/export", {
      method: "GET",
    });
  },
};

export interface ProgressSummary {
  solved_count: number;
  doing_count: number;
  total_problems: number;
  current_streak: number;
  activity_days: Record<string, number>;
  progress: Record<string, string>;
  notes: Record<string, string>;
  bookmarks: Array<{ item_type: string; item_id: string }>;
  visited_visualizers: string[];
  has_imported_local: boolean;
}

export const progressApi = {
  async getSummary(): Promise<ProgressSummary> {
    return await apiRequest<ProgressSummary>("/api/v1/progress/summary", { method: "GET" });
  },

  async updateProblem(
    slug: string,
    status: string,
    localDate?: string
  ): Promise<{ problem_slug: string; status: string; updated_at: string }> {
    return await apiRequest(`/api/v1/progress/problems/${encodeURIComponent(slug)}`, {
      method: "PUT",
      body: JSON.stringify({ status, local_date: localDate }),
    });
  },

  async updateNote(
    slug: string,
    text: string,
    localDate?: string
  ): Promise<{ problem_slug: string; text: string; updated_at: string }> {
    return await apiRequest(`/api/v1/progress/notes/${encodeURIComponent(slug)}`, {
      method: "PUT",
      body: JSON.stringify({ text, local_date: localDate }),
    });
  },

  async toggleBookmark(
    itemType: string,
    itemId: string
  ): Promise<{ item_type: string; item_id: string; bookmarked: boolean }> {
    return await apiRequest("/api/v1/progress/bookmarks/toggle", {
      method: "POST",
      body: JSON.stringify({ item_type: itemType, item_id: itemId }),
    });
  },

  async visitVisualizer(visualizerId: string): Promise<{ visualizer_id: string; visits: number }> {
    return await apiRequest(`/api/v1/progress/visualizers/${encodeURIComponent(visualizerId)}/visit`, {
      method: "POST",
    });
  },

  async importLocal(data: {
    progress: Record<string, string>;
    notes: Record<string, string>;
    quizzes: Record<string, number>;
    streak: number;
    activity_days: string[];
    visited_visualizers: string[];
    local_date?: string;
  }): Promise<ProgressSummary> {
    return await apiRequest<ProgressSummary>("/api/v1/progress/import-local", {
      method: "POST",
      body: JSON.stringify(data),
    });
  },
};

