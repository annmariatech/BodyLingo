export type AuthUser = {
  id: string;
  username: string;
  email: string;
  created_at: string;
  preferences?: Preferences;
  is_premium?: boolean;
};

export type Preferences = {
  topics: string[];
  situations: string[];
  explanation_style: string;
  communication_preferences: string[];
  cultural_contexts: string[];
  skipped: boolean;
};

export type AuthResult = {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  user: AuthUser;
};

export type LessonSummary = {
  id: string;
  title: string;
  description: string;
  topic: string;
  difficulty: string;
  estimated_duration_minutes: number;
  learning_objectives: string[];
  communication_context: string;
  is_premium?: boolean;
  locked?: boolean;
  completed?: boolean;
  recommendation_reason?: string;
};

export type LessonDetail = LessonSummary & {
  introduction: string;
  communication_cue: string;
  explanation: string;
  examples: { situation: string; possible_interpretation: string }[];
  knowledge_check: { question: string; options: string[] };
  key_takeaway: string;
};

export type LearningQuestion = {
  id: string;
  prompt: string;
  options: { id: string; text: string }[];
  explanation: string;
};

export type LearningProgress = {
  completed_lessons: string[];
  attempts: number;
  correct_answers: number;
  due_reviews: number;
  is_premium: boolean;
};

export type LearningReview = {
  lesson_id: string;
  lesson_title: string;
  question: LearningQuestion;
  due_at: string;
  is_due: boolean;
};

export type ScenarioSummary = {
  id: string;
  title: string;
  description?: string | null;
  learning_objectives: string[];
  media_placeholder: string;
};

export type ScenarioStep = {
  scenario_id: string;
  current_step: string;
  prompt: string;
  choices: { id: string; text: string }[];
};

export type ScenarioDetail = ScenarioStep & {
  title: string;
  description?: string | null;
  learning_objectives: string[];
  media_placeholder: string;
};

export type ScenarioResponse = {
  scenario_id: string;
  feedback?: string | null;
  current_step?: string | null;
  prompt?: string | null;
  choices: { id: string; text: string }[];
  completed: boolean;
};

export type ScenarioProgress = {
  completed_scenarios: string[];
  sessions: { scenario_id: string; title: string; is_completed: boolean; started_at: string; completed_at?: string | null; response_count: number }[];
};

const baseUrl = (import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000").replace(/\/$/, "");

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiRequest<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("bodylingo_access_token");
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(`${baseUrl}${path}`, { ...options, headers });
  } catch {
    throw new ApiError("Could not reach BodyLingo. Check that the backend is running.", 0);
  }

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      message = typeof body.detail === "string" ? body.detail : message;
    } catch {
      // Keep the status-based message when the response is not JSON.
    }
    if (response.status === 401) localStorage.removeItem("bodylingo_access_token");
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export function saveAuth(result: AuthResult): void {
  localStorage.setItem("bodylingo_access_token", result.access_token);
}

export function clearAuth(): void {
  localStorage.removeItem("bodylingo_access_token");
}
