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
    endpoint.includes("/auth/refresh") ||
    endpoint.includes("/auth/oauth");

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

  async loginWithClerk(clerkToken: string): Promise<UserProfile> {
    const res = await apiRequest<Record<string, unknown>>("/api/v1/auth/oauth/clerk", {
      method: "POST",
      body: JSON.stringify({
        clerk_token: clerkToken,
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

  async updateProfile(displayName: string): Promise<UserProfile> {
    const res = await apiRequest<Record<string, unknown>>("/api/v1/auth/me", {
      method: "PATCH",
      body: JSON.stringify({ display_name: displayName }),
    });
    return normalizeUser(res);
  },

  async changeEmail(newEmail: string, currentPassword: string): Promise<UserProfile> {
    const res = await apiRequest<Record<string, unknown>>("/api/v1/auth/email", {
      method: "POST",
      body: JSON.stringify({ new_email: newEmail, current_password: currentPassword }),
    });
    return normalizeUser(res);
  },

  async changePassword(currentPassword: string, newPassword: string): Promise<void> {
    await apiRequest("/api/v1/auth/password", {
      method: "POST",
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
  },

  async exportData(): Promise<Record<string, unknown>> {
    return await apiRequest<Record<string, unknown>>("/api/v1/auth/export", {
      method: "GET",
    });
  },
};

export interface RevisionItem {
  type: "problem" | "question";
  id: string;
  title: string;
  reason: string;
  due_stage: string;
  link: string;
}

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
  quiz_scores?: Record<string, number>;
  weakest_topics?: string[];
  revision_due?: RevisionItem[];
  preferred_language?: string;
  daily_goal?: { kind: string; label: string; target: number; permanent?: boolean } | null;
}

export interface DailyGoalPayload {
  kind: string;
  label: string;
  target: number;
  permanent?: boolean;
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

  async getSettings(): Promise<{ preferred_language: string; daily_goal: DailyGoalPayload | null }> {
    return await apiRequest("/api/v1/progress/settings", { method: "GET" });
  },

  async saveSettings(data: {
    preferred_language?: string;
    daily_goal?: DailyGoalPayload | null;
    clear_daily_goal?: boolean;
  }): Promise<{ preferred_language: string; daily_goal: DailyGoalPayload | null }> {
    const body: Record<string, unknown> = {};
    if (data.preferred_language !== undefined) body.preferred_language = data.preferred_language;
    if (data.clear_daily_goal) body.clear_daily_goal = true;
    else if (data.daily_goal !== undefined) body.daily_goal = data.daily_goal;
    return await apiRequest("/api/v1/progress/settings", {
      method: "PUT",
      body: JSON.stringify(body),
    });
  },

  async saveDailyGoal(goal: DailyGoalPayload | null): Promise<void> {
    if (goal === null) {
      await apiRequest("/api/v1/progress/settings", {
        method: "PUT",
        body: JSON.stringify({ clear_daily_goal: true }),
      });
      return;
    }
    await apiRequest("/api/v1/progress/settings", {
      method: "PUT",
      body: JSON.stringify({ daily_goal: goal }),
    });
  },
};

export interface TestCaseResult {
  label: string;
  passed: boolean;
  input: unknown;
  expected: unknown;
  actual: unknown;
  runtime_ms: number;
  error: string | null;
}

export interface JudgeResponse {
  verdict: "AC" | "WA" | "TLE" | "RE" | "CE";
  runtime_ms: number;
  test_results: TestCaseResult[];
  compile_output: string;
}

export interface SubmissionItem {
  id: string;
  problem_slug: string;
  language: string;
  verdict: "AC" | "WA" | "TLE" | "RE" | "CE";
  runtime_ms: number;
  test_results: TestCaseResult[];
  created_at: string;
}

export const judgeApi = {
  async runSamples(problemSlug: string, language: string, code: string): Promise<JudgeResponse> {
    return await apiRequest<JudgeResponse>("/api/v1/judge/run", {
      method: "POST",
      body: JSON.stringify({ problem_slug: problemSlug, language, code }),
    });
  },

  async submit(problemSlug: string, language: string, code: string): Promise<SubmissionItem> {
    return await apiRequest<SubmissionItem>("/api/v1/judge/submit", {
      method: "POST",
      body: JSON.stringify({ problem_slug: problemSlug, language, code }),
    });
  },

  async getSubmissions(problemSlug: string): Promise<SubmissionItem[]> {
    return await apiRequest<SubmissionItem[]>(
      `/api/v1/judge/submissions/${encodeURIComponent(problemSlug)}`,
      {
        method: "GET",
      }
    );
  },
};

export interface QuizQuestionItem {
  id: string;
  topic: string;
  subtopic: string | null;
  difficulty: string;
  prompt: string;
  options: string[];
}

export interface QuizGenerateResponse {
  attempt_id: string;
  questions: QuizQuestionItem[];
  total: number;
  is_mock?: boolean;
  duration_sec?: number | null;
  expires_at?: string | null;
}

export interface QuizQuestionResult {
  question_id: string;
  prompt: string;
  options: string[];
  selected_index: number | null;
  correct_index: number;
  is_correct: boolean;
  explanation: string;
}

export interface QuizSubmitResponse {
  attempt_id: string;
  total: number;
  correct: number;
  score_pct: number;
  duration_sec: number;
  results: QuizQuestionResult[];
}

export const quizApi = {
  async generateQuiz(
    topics: string[],
    count: number = 10,
    difficulty?: string,
    isMock: boolean = false,
    durationSec?: number,
    topicPlan?: [string, number][]
  ): Promise<QuizGenerateResponse> {
    return await apiRequest<QuizGenerateResponse>("/api/v1/quizzes/generate", {
      method: "POST",
      body: JSON.stringify({
        topics,
        count,
        difficulty,
        is_mock: isMock,
        duration_sec: durationSec,
        topic_plan: topicPlan ?? null,
      }),
    });
  },


  async submitQuiz(
    attemptId: string,
    durationSec: number,
    selected: Record<string, number>
  ): Promise<QuizSubmitResponse> {
    return await apiRequest<QuizSubmitResponse>(`/api/v1/quizzes/attempts/${encodeURIComponent(attemptId)}`, {
      method: "POST",
      body: JSON.stringify({ duration_sec: durationSec, selected }),
    });
  },

  async retryWrong(attemptId: string): Promise<QuizGenerateResponse> {
    return await apiRequest<QuizGenerateResponse>(
      `/api/v1/quizzes/attempts/${encodeURIComponent(attemptId)}/retry-wrong`,
      {
        method: "POST",
      }
    );
  },

  async getAttempt(attemptId: string): Promise<QuizSubmitResponse> {
    return await apiRequest<QuizSubmitResponse>(
      `/api/v1/quizzes/attempts/${encodeURIComponent(attemptId)}`,
      {
        method: "GET",
      }
    );
  },
};

export const contentApi = {
  async getProblems(params?: { topic?: string; difficulty?: string }): Promise<any[]> {
    const sp = new URLSearchParams();
    if (params?.topic) sp.append("topic", params.topic);
    if (params?.difficulty) sp.append("difficulty", params.difficulty);
    const qs = sp.toString() ? `?${sp.toString()}` : "";
    return await apiRequest<any[]>(`/api/v1/problems${qs}`);
  },

  async getProblem(slug: string): Promise<any> {
    return await apiRequest<any>(`/api/v1/problems/${encodeURIComponent(slug)}`);
  },

  async getQuestions(params?: { topic?: string; difficulty?: string }): Promise<any[]> {
    const sp = new URLSearchParams();
    if (params?.topic) sp.append("topic", params.topic);
    if (params?.difficulty) sp.append("difficulty", params.difficulty);
    const qs = sp.toString() ? `?${sp.toString()}` : "";
    return await apiRequest<any[]>(`/api/v1/questions${qs}`);
  },

  async getPaths(): Promise<any[]> {
    return await apiRequest<any[]>("/api/v1/paths");
  },

  async getPath(slug: string): Promise<any> {
    return await apiRequest<any>(`/api/v1/paths/${encodeURIComponent(slug)}`);
  },

  async getVisualizers(): Promise<any[]> {
    return await apiRequest<any[]>("/api/v1/visualizers");
  },

  async completeStep(stepId: number): Promise<{ step_id: number; completed: boolean }> {
    return await apiRequest<{ step_id: number; completed: boolean }>(
      `/api/v1/paths/steps/${stepId}/complete`,
      { method: "POST" }
    );
  },
};

export interface AdminStats {
  users_count: number;
  total_submissions: number;
  ac_submissions: number;
  ac_rate_pct: number;
  total_quiz_attempts: number;
  verified_questions: number;
  draft_questions: number;
  verified_problems: number;
  draft_problems: number;
}

export const adminApi = {
  async getStats(): Promise<AdminStats> {
    return await apiRequest<AdminStats>("/api/v1/admin/stats");
  },

  async getReviewQueue(type: "questions" | "problems" = "questions"): Promise<any[]> {
    return await apiRequest<any[]>(`/api/v1/admin/review-queue?type=${encodeURIComponent(type)}`);
  },

  async reviewQuestion(
    id: string,
    action: "approved" | "rejected" | "edited",
    note?: string
  ): Promise<any> {
    return await apiRequest(`/api/v1/admin/questions/${encodeURIComponent(id)}/review`, {
      method: "POST",
      body: JSON.stringify({ action, note }),
    });
  },

  async reviewProblem(slug: string, action: "approved" | "rejected", note?: string): Promise<any> {
    return await apiRequest(`/api/v1/admin/problems/${encodeURIComponent(slug)}/review`, {
      method: "POST",
      body: JSON.stringify({ action, note }),
    });
  },

  async getCoverage(): Promise<{ matrix: Record<string, Record<string, number>>; total_verified: number }> {
    return await apiRequest("/api/v1/admin/coverage");
  },

  async getAuditLogs(): Promise<any[]> {
    return await apiRequest<any[]>("/api/v1/admin/audit-logs");
  },
};



