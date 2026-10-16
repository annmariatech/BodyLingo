import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import App from "./App";

const preferences = { topics: [], situations: [], explanation_style: "balanced", communication_preferences: [], cultural_contexts: [], skipped: true };
const user = { id: "user-1", username: "ann", email: "ann@example.com", created_at: "2026-10-17T00:00:00Z", preferences, is_premium: false };

afterEach(() => {
  cleanup();
  localStorage.clear();
  vi.restoreAllMocks();
});

describe("BodyLingo foundation", () => {
  it("shows account sign-in and registration options", () => {
    render(<App />);
    expect(screen.getByRole("heading", { name: "Welcome back" })).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Create an account" }));
    expect(screen.getByRole("heading", { name: "Create your account" })).toBeInTheDocument();
    expect(screen.getByLabelText("Username")).toBeInTheDocument();
  });

  it("signs in and preserves the required five-screen navigation order", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input) => {
      const url = String(input);
      if (url.endsWith("/api/auth/login")) {
        return new Response(JSON.stringify({ access_token: "token", token_type: "bearer", expires_in: 1800, user }), { status: 200 });
      }
      if (url.endsWith("/api/learning/recommendations")) return new Response("[]", { status: 200 });
      if (url.endsWith("/api/learning/progress")) return new Response(JSON.stringify({ completed_lessons: [], attempts: 0, correct_answers: 0, due_reviews: 0, is_premium: false }), { status: 200 });
      if (url.endsWith("/api/learning/reviews")) return new Response("[]", { status: 200 });
      if (url.endsWith("/api/auth/me")) return new Response(JSON.stringify(user), { status: 200 });
      return new Response(null, { status: 204 });
    });
    const actor = userEvent.setup();
    render(<App />);
    await actor.type(screen.getByLabelText("Email or username"), "ann@example.com");
    await actor.type(screen.getByLabelText("Password"), "strong-password");
    await actor.click(screen.getByRole("button", { name: "Sign in" }));
    await screen.findByRole("heading", { name: /grow your understanding/i });
    const nav = screen.getByRole("navigation", { name: "Main navigation" });
    expect(Array.from(nav.querySelectorAll("button span:nth-child(2)")).map((el) => el.textContent)).toEqual([
      "Learning", "Scenario", "Chatbot", "Forum", "Profile",
    ]);
    await actor.click(within(nav).getByRole("button", { name: /Scenario/ }));
    expect(screen.getByRole("heading", { name: /try a moment from everyday life/i })).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalled();
  });

  it("restores a valid saved session", async () => {
    localStorage.setItem("bodylingo_access_token", "saved-token");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(new Response(JSON.stringify(user), { status: 200 }));
    render(<App />);
    await waitFor(() => expect(screen.getByRole("button", { name: "Open profile" })).toBeInTheDocument());
  });

  it("saves optional onboarding preferences and continues into learning", async () => {
    const registered = { ...user, preferences: undefined };
    vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
      const url = String(input);
      if (url.endsWith("/api/auth/register")) return new Response(JSON.stringify({ access_token: "new-token", token_type: "bearer", expires_in: 1800, user: registered }), { status: 201 });
      if (url.endsWith("/api/learning/preferences")) return new Response(String(init?.body), { status: 200 });
      if (url.endsWith("/api/learning/recommendations")) return new Response("[]", { status: 200 });
      if (url.endsWith("/api/learning/progress")) return new Response(JSON.stringify({ completed_lessons: [], attempts: 0, correct_answers: 0, due_reviews: 0, is_premium: false }), { status: 200 });
      if (url.endsWith("/api/learning/reviews")) return new Response("[]", { status: 200 });
      return new Response(null, { status: 204 });
    });
    const actor = userEvent.setup();
    render(<App />);
    await actor.click(screen.getByRole("button", { name: "Create an account" }));
    await actor.type(screen.getByLabelText("Username"), "ann");
    await actor.type(screen.getByLabelText("Email"), "ann@example.com");
    await actor.type(screen.getByLabelText("Password"), "safe-learning-password");
    await actor.click(screen.getByRole("button", { name: /create account/i }));
    expect(await screen.findByRole("heading", { name: "What would you like to explore?" })).toBeInTheDocument();
    await actor.click(screen.getByRole("checkbox", { name: "Eye contact" }));
    await actor.click(screen.getByRole("button", { name: /save and continue/i }));
    expect(await screen.findByRole("heading", { name: /grow your understanding/i })).toBeInTheDocument();
  });
});
