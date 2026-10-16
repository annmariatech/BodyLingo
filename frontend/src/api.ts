export type AuthUser = {
  id: string;
  username: string;
  email: string;
  created_at: string;
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
