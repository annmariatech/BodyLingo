import { useEffect, useState, type FormEvent } from "react";
import {
  BookOpen,
  Check,
  ChevronRight,
  Compass,
  Heart,
  LogOut,
  MessageCircle,
  Search,
  ShieldCheck,
  Sparkles,
  UsersRound,
} from "lucide-react";
import { apiRequest, clearAuth, saveAuth, type AuthResult, type AuthUser, type LessonSummary } from "./api";

type Screen = "Learning" | "Scenario" | "Chatbot" | "Forum" | "Profile";
const screens: { name: Screen; icon: typeof BookOpen }[] = [
  { name: "Learning", icon: BookOpen },
  { name: "Scenario", icon: Compass },
  { name: "Chatbot", icon: MessageCircle },
  { name: "Forum", icon: UsersRound },
  { name: "Profile", icon: Heart },
];

function AuthScreen({ onAuthenticated }: { onAuthenticated: (user: AuthUser) => void }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    try {
      const result = await apiRequest<AuthResult>(`/api/auth/${mode === "login" ? "login" : "register"}`, {
        method: "POST",
        body: JSON.stringify(mode === "login" ? { identifier: email, password } : { username, email, password }),
      });
      saveAuth(result);
      onAuthenticated(result.user);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Something went wrong. Try again.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="auth-layout">
      <section className="auth-story">
        <a className="brand" href="#home" aria-label="BodyLingo home"><span className="brand-mark">b.</span> bodylingo</a>
        <div className="auth-message">
          <div className="mascot-bubble" aria-hidden="true">🐧</div>
          <p className="eyebrow">COMMUNICATION, WITH CARE</p>
          <h1>There’s more than one way to connect.</h1>
          <p className="story-copy">Explore social cues with curiosity, context, and room for everyone to be themselves.</p>
          <div className="story-note"><Heart size={17} /> No assumptions. Just understanding.</div>
        </div>
        <span className="auth-decoration auth-decoration-one" />
        <span className="auth-decoration auth-decoration-two" />
      </section>
      <section className="auth-panel">
        <div className="auth-card">
          <p className="eyebrow">YOUR LEARNING SPACE</p>
          <h2>{mode === "login" ? "Welcome back" : "Create your account"}</h2>
          <p className="muted">{mode === "login" ? "Pick up your learning journey whenever you’re ready." : "A gentle place to learn at your own pace."}</p>
          <form onSubmit={submit} className="auth-form">
            {mode === "register" && <label>Username<input autoComplete="username" minLength={3} maxLength={24} pattern="[A-Za-z0-9_]+" required value={username} onChange={(event) => setUsername(event.target.value)} placeholder="Choose a username" /></label>}
            <label>{mode === "login" ? "Email or username" : "Email"}<input autoComplete={mode === "login" ? "username" : "email"} type={mode === "login" ? "text" : "email"} required value={email} onChange={(event) => setEmail(event.target.value)} placeholder={mode === "login" ? "you@example.com or username" : "you@example.com"} /></label>
            <label>Password<input autoComplete={mode === "login" ? "current-password" : "new-password"} type="password" minLength={mode === "register" ? 10 : 1} maxLength={128} required value={password} onChange={(event) => setPassword(event.target.value)} placeholder={mode === "register" ? "At least 10 characters" : "Your password"} /></label>
            {error && <p className="form-error" role="alert">{error}</p>}
            <button className="button button-primary auth-submit" disabled={busy}>{busy ? "One moment…" : mode === "login" ? "Sign in" : "Create account"}<ChevronRight size={18} /></button>
          </form>
          <p className="auth-switch">{mode === "login" ? "New to BodyLingo?" : "Already have an account?"} <button onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}>{mode === "login" ? "Create an account" : "Sign in"}</button></p>
          <div className="privacy-note"><ShieldCheck size={15} /> Your communication preferences are always yours to share or keep private.</div>
        </div>
      </section>
    </main>
  );
}

function LearningScreen() {
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [error, setError] = useState("");
  useEffect(() => {
    apiRequest<LessonSummary[]>("/api/lessons")
      .then(setLessons)
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Lessons are unavailable."));
  }, []);

  return <>
    <div className="welcome-banner">
      <div><p className="eyebrow">YOUR LEARNING PATH</p><h1>Grow your understanding, one moment at a time.</h1><p>Small lessons. More generous interpretations.</p></div>
      <div className="banner-penguin" aria-hidden="true">🐧<span>Hi, I’m Pip!</span></div>
      <div className="banner-doodle doodle-one">✳</div><div className="banner-doodle doodle-two">✦</div>
    </div>
    <div className="section-heading"><div><p className="eyebrow">START EXPLORING</p><h2>Lessons for real life</h2></div><button className="text-button" aria-label="Search lessons"><Search size={17} /> Explore topics</button></div>
    {error && <p className="inline-error" role="alert">{error}</p>}
    <div className="lesson-grid">
      {lessons.map((lesson, index) => <article className={`lesson-card lesson-tone-${index % 4}`} key={lesson.id}>
        <div className="lesson-card-top"><span className="lesson-icon"><BookOpen size={20} /></span><span className="lesson-duration">{lesson.estimated_duration_minutes} min</span></div>
        <p className="lesson-topic">{lesson.topic}</p><h3>{lesson.title}</h3><p className="lesson-description">{lesson.description}</p>
        <div className="lesson-card-bottom"><span className="difficulty">{lesson.difficulty}</span><button aria-label={`Open ${lesson.title}`} className="round-arrow"><ChevronRight size={18} /></button></div>
      </article>)}
    </div>
    {!lessons.length && !error && <div className="loading-card"><span className="loading-dot" /> Finding your first lessons…</div>}
    <div className="gentle-reminder"><Sparkles size={18} /><p><strong>A gentle reminder:</strong> cues can have many meanings. Curiosity is a better starting point than certainty.</p></div>
  </>;
}

function ComingSoon({ screen }: { screen: Exclude<Screen, "Learning" | "Profile"> }) {
  const messages = {
    Scenario: { icon: Compass, eyebrow: "PRACTICE WITH POSSIBILITY", title: "Try a moment from everyday life", copy: "Interactive scenarios are part of the next learning phase. You’ll be able to explore choices and their possible effects." },
    Chatbot: { icon: MessageCircle, eyebrow: "A CURIOUS CONVERSATION", title: "Questions are welcome here", copy: "Your learning companion is coming soon. For now, explore the lesson cards and keep your questions close." },
    Forum: { icon: UsersRound, eyebrow: "LEARN IN COMMUNITY", title: "Many perspectives make room", copy: "A read-only community space with thoughtfully chosen topics is on its way." },
  }[screen];
  const Icon = messages.icon;
  return <section className="coming-card"><div className="coming-illustration"><span className="coming-halo" /><Icon size={38} strokeWidth={1.4} /><span className="coming-star">✦</span></div><p className="eyebrow">{messages.eyebrow}</p><h1>{messages.title}</h1><p>{messages.copy}</p><span className="phase-pill"><Check size={14} /> Foundation phase</span></section>;
}

function ProfileScreen({ user, onLogout }: { user: AuthUser; onLogout: () => void }) {
  return <section className="profile-layout"><div className="profile-title"><p className="eyebrow">YOUR SPACE</p><h1>Profile & preferences</h1><p>Make this learning experience feel like yours.</p></div><article className="profile-card"><div className="profile-avatar">{user.username.slice(0, 1).toUpperCase()}</div><div className="profile-identity"><h2>{user.username}</h2><p>{user.email}</p></div><span className="profile-badge"><ShieldCheck size={15} /> Account</span></article><article className="preferences-card"><div className="preferences-icon"><Heart size={19} /></div><div><h3>Your preferences, your choice</h3><p>Preference editing and personalized learning paths are coming in the learning phase. You never need to share a diagnosis to use BodyLingo.</p></div></article><button className="button button-quiet logout-button" onClick={onLogout}><LogOut size={17} /> Sign out</button></section>;
}

function AppShell({ user, onLogout }: { user: AuthUser; onLogout: () => void }) {
  const [screen, setScreen] = useState<Screen>("Learning");
  return <div className="app-shell">
    <aside className="sidebar"><a className="brand" href="#home"><span className="brand-mark">b.</span> bodylingo</a><div className="sidebar-label">YOUR SPACE</div><nav aria-label="Main navigation" className="side-nav">{screens.map(({ name, icon: Icon }) => <button key={name} className={`nav-link ${screen === name ? "active" : ""}`} aria-current={screen === name ? "page" : undefined} onClick={() => setScreen(name)}><Icon size={19} strokeWidth={1.8} /><span>{name}</span>{name === "Learning" && <span className="nav-dot" />}</button>)}</nav><div className="sidebar-bottom"><div className="sidebar-mascot">🐧<div><strong>You’ve got this!</strong><span>Curiosity looks good on you.</span></div></div><button className="user-mini" onClick={() => setScreen("Profile")}><span className="mini-avatar">{user.username.slice(0, 1).toUpperCase()}</span><span><strong>{user.username}</strong><small>My profile</small></span><ChevronRight size={16} /></button></div></aside>
    <main className="main-column"><header className="topbar"><div className="mobile-brand"><span className="brand-mark">b.</span> bodylingo</div><span className="topbar-greeting">A little more understanding, every day <span>✦</span></span><button className="top-avatar" aria-label="Open profile" onClick={() => setScreen("Profile")}>{user.username.slice(0, 1).toUpperCase()}</button></header><div className="content-area" key={screen}>{screen === "Learning" ? <LearningScreen /> : screen === "Profile" ? <ProfileScreen user={user} onLogout={onLogout} /> : <ComingSoon screen={screen} />}</div></main>
    <nav aria-label="Mobile navigation" className="bottom-nav">{screens.map(({ name, icon: Icon }) => <button key={name} className={screen === name ? "selected" : ""} aria-current={screen === name ? "page" : undefined} onClick={() => setScreen(name)}><Icon size={20} /><span>{name}</span></button>)}</nav>
  </div>;
}

export default function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checking, setChecking] = useState(true);
  useEffect(() => {
    if (!localStorage.getItem("bodylingo_access_token")) {
      setChecking(false);
      return;
    }
    apiRequest<AuthUser>("/api/auth/me")
      .then(setUser)
      .catch(() => clearAuth())
      .finally(() => setChecking(false));
  }, []);

  async function logout() {
    try { await apiRequest<void>("/api/auth/logout", { method: "POST" }); } catch { /* Local sign-out still works if the API is offline. */ }
    clearAuth();
    setUser(null);
  }

  if (checking) return <div className="app-loading"><span className="loading-dot" /> Opening your space…</div>;
  if (!user) return <AuthScreen onAuthenticated={setUser} />;
  return <AppShell user={user} onLogout={logout} />;
}
