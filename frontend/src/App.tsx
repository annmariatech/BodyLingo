import { useEffect, useState, type FormEvent } from "react";
import {
  BookOpen,
  Check,
  ChevronRight,
  Compass,
  Heart,
  LogOut,
  MessageCircle,
  ShieldCheck,
  Sparkles,
  UsersRound,
} from "lucide-react";
import { apiRequest, clearAuth, saveAuth, type AuthResult, type AuthUser, type LessonSummary, type LessonDetail, type LearningQuestion, type LearningProgress, type LearningReview, type Preferences, type ScenarioDetail, type ScenarioProgress, type ScenarioResponse, type ScenarioStep, type ScenarioSummary } from "./api";

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

function LearningScreen({ onProgress }: { onProgress: (progress: LearningProgress) => void }) {
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [progress, setProgress] = useState<LearningProgress | null>(null);
  const [reviews, setReviews] = useState<LearningReview[]>([]);
  const [error, setError] = useState("");
  const [activeLesson, setActiveLesson] = useState<LessonDetail | null>(null);
  const [questions, setQuestions] = useState<LearningQuestion[]>([]);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [selectedOption, setSelectedOption] = useState("");
  const [feedback, setFeedback] = useState<{ correct: boolean; explanation: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [recommendationError, setRecommendationError] = useState("");

  async function refresh() {
    try {
      const [catalog, currentProgress, scheduledReviews] = await Promise.all([
        apiRequest<LessonSummary[]>("/api/learning/recommendations"),
        apiRequest<LearningProgress>("/api/learning/progress"),
        apiRequest<LearningReview[]>("/api/learning/reviews"),
      ]);
      setLessons(catalog);
      setProgress(currentProgress);
      setReviews(scheduledReviews);
      onProgress(currentProgress);
      setError("");
    } catch (cause) {
      setRecommendationError(cause instanceof Error ? cause.message : "Learning data is unavailable.");
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

  async function openLesson(lessonId: string, reviewQuestionId?: string) {
    setBusy(true);
    setError("");
    try {
      const [lesson, quiz] = await Promise.all([
        apiRequest<LessonDetail>(`/api/lessons/${lessonId}`),
        apiRequest<LearningQuestion[]>(`/api/learning/lessons/${lessonId}/questions`),
      ]);
      setActiveLesson(lesson);
      setQuestions(quiz);
      setQuestionIndex(reviewQuestionId ? Math.max(0, quiz.findIndex((item) => item.id === reviewQuestionId)) : 0);
      setSelectedOption("");
      setFeedback(null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "This lesson could not be opened.");
    } finally {
      setBusy(false);
    }
  }

  async function answerQuestion() {
    const question = questions[questionIndex];
    if (!question || !selectedOption) return;
    setBusy(true);
    try {
      const result = await apiRequest<{ correct: boolean; explanation: string; completed: boolean }>(
        `/api/learning/lessons/${activeLesson?.id}/attempts/${question.id}`,
        { method: "POST", body: JSON.stringify({ question_id: question.id, selected_option_id: selectedOption }) },
      );
      setFeedback(result);
      if (result.correct) await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Your answer could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  function nextQuestion() {
    if (questionIndex + 1 >= questions.length) {
      setActiveLesson(null);
      void refresh();
      return;
    }
    setQuestionIndex((index) => index + 1);
    setSelectedOption("");
    setFeedback(null);
  }

  if (activeLesson) {
    const question = questions[questionIndex];
    return <section className="lesson-view">
      <button className="text-button lesson-back" onClick={() => setActiveLesson(null)}>← Back to lessons</button>
      <p className="eyebrow">{activeLesson.topic} · {activeLesson.estimated_duration_minutes} MIN</p>
      <h1>{activeLesson.title}</h1>
      <p className="lesson-introduction">{activeLesson.introduction}</p>
      <article className="lesson-teaching"><span className="eyebrow">A CUE TO NOTICE</span><h2>{activeLesson.communication_cue}</h2><p>{activeLesson.explanation}</p><strong>{activeLesson.key_takeaway}</strong></article>
      {question && <article className="quiz-card">
        <div className="quiz-progress">QUESTION {questionIndex + 1} OF {questions.length}</div>
        <h2>{question.prompt}</h2>
        <div className="quiz-options" role="radiogroup" aria-label="Answer choices">
          {question.options.map((option) => <button key={option.id} role="radio" aria-checked={selectedOption === option.id} className={`quiz-option ${selectedOption === option.id ? "chosen" : ""}`} disabled={Boolean(feedback)} onClick={() => setSelectedOption(option.id)}>{option.text}</button>)}
        </div>
        {feedback && <p className={`quiz-feedback ${feedback.correct ? "right" : "try-again"}`} role="status"><strong>{feedback.correct ? "That’s right." : "Not quite yet."}</strong> {feedback.explanation}</p>}
        {!feedback ? <button className="button button-primary" disabled={!selectedOption || busy} onClick={() => void answerQuestion()}>{busy ? "Saving…" : "Check answer"}</button> : feedback.correct ? <button className="button button-primary" onClick={nextQuestion}>{questionIndex + 1 === questions.length ? "Finish lesson" : "Next question"}<ChevronRight size={16} /></button> : <button className="button button-primary" onClick={() => { setFeedback(null); setSelectedOption(""); }}>Try again</button>}
      </article>}
    </section>;
  }

  return <>
    <div className="welcome-banner">
      <div><p className="eyebrow">YOUR LEARNING PATH</p><h1>Grow your understanding, one moment at a time.</h1><p>Small lessons. More generous interpretations.</p></div>
      <div className="banner-penguin" aria-hidden="true">🐧<span>Hi, I’m Pip!</span></div>
      <div className="banner-doodle doodle-one">✳</div><div className="banner-doodle doodle-two">✦</div>
    </div>
    {progress && <div className="learning-progress"><span><strong>{progress.completed_lessons.length}</strong> lessons completed</span><span><strong>{progress.correct_answers}</strong> correct answers</span><span><strong>{progress.due_reviews}</strong> reviews due</span></div>}
    {reviews.length > 0 && <section className="review-panel"><div><p className="eyebrow">SPACED PRACTICE</p><h2>Questions to revisit</h2><p>Incorrect answers return here on a gentle schedule. Answering a review correctly spaces the next revisit further out.</p></div><div className="review-list">{reviews.map((review) => <button key={`${review.lesson_id}-${review.question.id}`} onClick={() => void openLesson(review.lesson_id, review.question.id)} disabled={!review.is_due} className="review-item"><span>{review.is_due ? "Ready to review" : `Due ${new Date(review.due_at).toLocaleDateString()}`}</span><strong>{review.lesson_title}</strong><small>{review.question.prompt}</small></button>)}</div></section>}
    <div className="section-heading"><div><p className="eyebrow">CHOSEN FOR YOU</p><h2>Lessons for real life</h2></div><span className="recommendation-label"><Sparkles size={15} /> Personalised path</span></div>
    {error && <p className="inline-error" role="alert">{error}</p>}
    {recommendationError && <p className="inline-error" role="alert">{recommendationError}</p>}
    <div className="lesson-grid">
      {lessons.map((lesson, index) => <article className={`lesson-card lesson-tone-${index % 4} ${lesson.locked ? "locked" : ""}`} key={lesson.id}>
        <div className="lesson-card-top"><span className="lesson-icon"><BookOpen size={20} /></span><span className="lesson-duration">{lesson.estimated_duration_minutes} min</span></div>
        <p className="lesson-topic">{lesson.topic}{lesson.is_premium ? " · PREMIUM" : ""}</p><h3>{lesson.title}</h3><p className="lesson-description">{lesson.description}</p><small className="recommendation-reason">{lesson.recommendation_reason}</small>
        <div className="lesson-card-bottom"><span className="difficulty">{lesson.completed ? "completed" : lesson.difficulty}</span><button aria-label={`${lesson.locked ? "Locked" : "Open"} ${lesson.title}`} className="round-arrow" disabled={lesson.locked || busy} onClick={() => void openLesson(lesson.id)}>{lesson.locked ? <ShieldCheck size={16} /> : <ChevronRight size={18} />}</button></div>
      </article>)}
    </div>
    {!lessons.length && !error && <div className="loading-card"><span className="loading-dot" /> Finding your first lessons…</div>}
    <div className="gentle-reminder"><Sparkles size={18} /><p><strong>A gentle reminder:</strong> cues can have many meanings. Curiosity is a better starting point than certainty.</p></div>
  </>;
}

function ScenarioScreen() {
  const [scenarios, setScenarios] = useState<ScenarioSummary[]>([]);
  const [completed, setCompleted] = useState<string[]>([]);
  const [active, setActive] = useState<ScenarioDetail | null>(null);
  const [step, setStep] = useState<ScenarioStep | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [isComplete, setIsComplete] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function refresh() {
    try {
      const [catalog, history] = await Promise.all([
        apiRequest<{ scenarios: ScenarioSummary[] }>("/api/scenarios"),
        apiRequest<ScenarioProgress>("/api/scenarios/progress"),
      ]);
      setScenarios(catalog.scenarios);
      setCompleted(history.completed_scenarios);
      setError("");
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Scenarios are unavailable.");
    }
  }

  useEffect(() => { void refresh(); }, []);

  async function startScenario(scenario: ScenarioSummary) {
    setBusy(true);
    try {
      const detail = await apiRequest<ScenarioDetail>(`/api/scenarios/${scenario.id}`);
      setActive(detail);
      setStep(detail);
      setFeedback(null);
      setIsComplete(false);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "This scenario could not be opened.");
    } finally {
      setBusy(false);
    }
  }

  async function choose(choiceId: string) {
    if (!active || !step) return;
    setBusy(true);
    setError("");
    try {
      const result = await apiRequest<ScenarioResponse>(`/api/scenarios/${active.scenario_id}/respond`, {
        method: "POST",
        body: JSON.stringify({ current_step: step.current_step, choice_id: choiceId }),
      });
      setFeedback(result.feedback ?? "Your choice has been recorded.");
      setIsComplete(result.completed);
      setStep(result.completed ? null : {
        scenario_id: result.scenario_id,
        current_step: result.current_step ?? "",
        prompt: result.prompt ?? "",
        choices: result.choices,
      });
      if (result.completed) await refresh();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Your choice could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  if (active) return <section className="scenario-view">
    <button className="text-button scenario-back" onClick={() => { setActive(null); setStep(null); setFeedback(null); void refresh(); }}>← Scenario library</button>
    <p className="eyebrow">PRACTICE WITH POSSIBILITY</p>
    <h1>{active.title}</h1>
    {active.description && <p className="scenario-description">{active.description}</p>}
    <div className="scenario-objectives"><strong>What you’ll practise</strong><ul>{active.learning_objectives.map((objective) => <li key={objective}>{objective}</li>)}</ul></div>
    <p className="scenario-media-note"><Compass size={15} /> {active.media_placeholder}</p>
    {step && <article className="scenario-step"><span className="quiz-progress">A MOMENT TO CONSIDER</span><h2>{step.prompt}</h2><div className="scenario-choices">{step.choices.map((choice) => <button key={choice.id} className="scenario-choice" disabled={busy || Boolean(feedback)} onClick={() => void choose(choice.id)}>{choice.text}<ChevronRight size={16} /></button>)}</div></article>}
    {feedback && <article className={`scenario-feedback ${isComplete ? "finished" : ""}`} role="status"><span className="scenario-feedback-mascot" aria-hidden="true">🐧</span><div><strong>{isComplete ? "Scenario complete" : "A possible outcome"}</strong><p>{feedback}</p>{isComplete ? <button className="button button-primary" onClick={() => { setActive(null); setStep(null); setFeedback(null); }}>Back to scenarios</button> : <button className="button button-primary" onClick={() => setFeedback(null)}>Continue<ChevronRight size={16} /></button>}</div></article>}
    {error && <p className="inline-error" role="alert">{error}</p>}
  </section>;

  return <section className="scenario-library"><div className="scenario-hero"><p className="eyebrow">PRACTICE WITH POSSIBILITY</p><h1>Try a moment from everyday life.</h1><p>Explore different responses and their possible effects. There is room for context, individual preferences, and respectful clarification.</p><span aria-hidden="true">🐧</span></div>
    {error && <p className="inline-error" role="alert">{error}</p>}
    <div className="section-heading"><div><p className="eyebrow">BRANCHING PRACTICE</p><h2>Choose a scenario</h2></div><span className="recommendation-label">Progress is saved to your account</span></div>
    <div className="scenario-grid">{scenarios.map((scenario, index) => <article className={`scenario-card scenario-tone-${index % 4}`} key={scenario.id}><div className="scenario-card-icon"><Compass size={20} /></div><p className="scenario-topic">EVERYDAY PRACTICE</p><h2>{scenario.title}</h2><p>{scenario.description}</p><ul>{scenario.learning_objectives.slice(0, 2).map((objective) => <li key={objective}>{objective}</li>)}</ul><span className="scenario-asset-note">{scenario.media_placeholder}</span><button className="button button-primary" disabled={busy} onClick={() => void startScenario(scenario)}>{completed.includes(scenario.id) ? "Practise again" : "Start scenario"}<ChevronRight size={16} /></button></article>)}</div>
    {!scenarios.length && !error && <div className="loading-card"><span className="loading-dot" /> Loading scenarios…</div>}
  </section>;
}

function ComingSoon({ screen }: { screen: "Chatbot" | "Forum" }) {
  const messages = {
    Chatbot: { icon: MessageCircle, eyebrow: "A CURIOUS CONVERSATION", title: "Questions are welcome here", copy: "Your learning companion is coming soon. For now, explore the lesson cards and keep your questions close." },
    Forum: { icon: UsersRound, eyebrow: "LEARN IN COMMUNITY", title: "Many perspectives make room", copy: "A read-only community space with thoughtfully chosen topics is on its way." },
  }[screen];
  const Icon = messages.icon;
  return <section className="coming-card"><div className="coming-illustration"><span className="coming-halo" /><Icon size={38} strokeWidth={1.4} /><span className="coming-star">✦</span></div><p className="eyebrow">{messages.eyebrow}</p><h1>{messages.title}</h1><p>{messages.copy}</p><span className="phase-pill"><Check size={14} /> Foundation phase</span></section>;
}

const preferenceChoices = {
  topics: ["Facial expressions", "Tone of voice", "Eye contact", "Personal space and breaks", "Gestures and culture", "Clarifying needs"],
  situations: ["Everyday conversations", "Friendships", "Meetings and teamwork", "New cultural settings", "Busy or noisy places"],
  communication_preferences: ["Written steps", "Extra time to think", "Direct language", "Lower sensory load", "Knowing the plan ahead"],
  cultural_contexts: ["Japan", "Western Europe", "North America", "South Asia", "Explore varied contexts"],
};

function PreferenceGroup({ title, choices, selected, onChange }: { title: string; choices: string[]; selected: string[]; onChange: (value: string[]) => void }) {
  return <fieldset className="preference-group"><legend>{title}</legend><div className="preference-options">{choices.map((choice) => <label key={choice} className={`preference-choice ${selected.includes(choice) ? "checked" : ""}`}><input type="checkbox" checked={selected.includes(choice)} onChange={(event) => onChange(event.target.checked ? [...selected, choice] : selected.filter((item) => item !== choice))} />{choice}</label>)}</div></fieldset>;
}

function OnboardingScreen({ initial, onSaved }: { initial?: Partial<Preferences>; onSaved: (preferences: Preferences) => Promise<void> }) {
  const [topics, setTopics] = useState(initial?.topics ?? []);
  const [situations, setSituations] = useState(initial?.situations ?? []);
  const [communication, setCommunication] = useState(initial?.communication_preferences ?? []);
  const [cultures, setCultures] = useState(initial?.cultural_contexts ?? []);
  const [style, setStyle] = useState(initial?.explanation_style ?? "balanced");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function save(skipped: boolean) {
    setBusy(true);
    setError("");
    try {
      await onSaved({ topics, situations, explanation_style: style, communication_preferences: communication, cultural_contexts: cultures, skipped });
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Your preferences could not be saved.");
    } finally {
      setBusy(false);
    }
  }

  return <section className="onboarding-layout"><div className="onboarding-heading"><div className="onboarding-penguin" aria-hidden="true">🐧</div><p className="eyebrow">A PATH THAT FITS YOU</p><h1>What would you like to explore?</h1><p>Choose anything that feels useful. These preferences shape lesson recommendations; you can change them later. No diagnosis or personal explanation is needed.</p></div>
    <div className="onboarding-groups">
      <PreferenceGroup title="Topics" choices={preferenceChoices.topics} selected={topics} onChange={setTopics} />
      <PreferenceGroup title="Situations to practise" choices={preferenceChoices.situations} selected={situations} onChange={setSituations} />
      <fieldset className="preference-group"><legend>Explanation style</legend><div className="style-options">{[["balanced", "A mix of examples and clear steps"], ["examples", "More examples"], ["concise", "Short and direct"]].map(([value, label]) => <label key={value}><input type="radio" name="explanation-style" value={value} checked={style === value} onChange={() => setStyle(value)} />{label}</label>)}</div></fieldset>
      <PreferenceGroup title="Communication preferences (optional)" choices={preferenceChoices.communication_preferences} selected={communication} onChange={setCommunication} />
      <PreferenceGroup title="Cultural contexts to learn about (optional)" choices={preferenceChoices.cultural_contexts} selected={cultures} onChange={setCultures} />
    </div>
    {error && <p className="form-error" role="alert">{error}</p>}
    <div className="onboarding-actions"><button className="button button-quiet" disabled={busy} onClick={() => void save(true)}>Skip for now</button><button className="button button-primary" disabled={busy} onClick={() => void save(false)}>{busy ? "Saving…" : "Save and continue"}<ChevronRight size={17} /></button></div>
  </section>;
}

function ProfileScreen({ user, onLogout, onEdit, progress }: { user: AuthUser; onLogout: () => void; onEdit: () => void; progress: LearningProgress | null }) {
  const preferences = user.preferences;
  return <section className="profile-layout"><div className="profile-title"><p className="eyebrow">YOUR SPACE</p><h1>Profile & preferences</h1><p>Make this learning experience feel like yours.</p></div><article className="profile-card"><div className="profile-avatar">{user.username.slice(0, 1).toUpperCase()}</div><div className="profile-identity"><h2>{user.username}</h2><p>{user.email}</p></div><span className="profile-badge"><ShieldCheck size={15} /> Account</span></article>
    <article className="preferences-card"><div className="preferences-icon"><Heart size={19} /></div><div><h3>Your learning preferences</h3><p>{preferences?.topics?.length ? preferences.topics.join(" · ") : "No topics selected yet. You can skip preferences and still use every free lesson."}</p>{preferences?.cultural_contexts?.length ? <p>Cultural contexts: {preferences.cultural_contexts.join(", ")}</p> : null}<button className="text-button profile-edit" onClick={onEdit}>Edit preferences</button></div></article>
    <article className="profile-progress"><h3>Learning progress</h3><div><span>{progress?.completed_lessons.length ?? "—"}<small>completed lessons</small></span><span>{progress?.correct_answers ?? "—"}<small>correct answers</small></span><span>{progress?.due_reviews ?? "—"}<small>reviews due</small></span></div><p>{user.is_premium ? "Demo premium enabled" : "Free learning access"}</p></article>
    <button className="button button-quiet logout-button" onClick={onLogout}><LogOut size={17} /> Sign out</button></section>;
}

function AppShell({ user, onUserUpdate, onLogout, onboardingPending }: { user: AuthUser; onUserUpdate: (user: AuthUser) => void; onLogout: () => void; onboardingPending: boolean }) {
  const [screen, setScreen] = useState<Screen>("Learning");
  const [showOnboarding, setShowOnboarding] = useState(onboardingPending);
  const [returnToProfile, setReturnToProfile] = useState(false);
  const [progress, setProgress] = useState<LearningProgress | null>(null);

  async function savePreferences(preferences: Preferences) {
    const saved = await apiRequest<Preferences>("/api/learning/preferences", { method: "PUT", body: JSON.stringify(preferences) });
    onUserUpdate({ ...user, preferences: saved });
    setShowOnboarding(false);
    setScreen(returnToProfile ? "Profile" : "Learning");
    setReturnToProfile(false);
  }

  return <div className="app-shell">
    <aside className="sidebar"><a className="brand" href="#home"><span className="brand-mark">b.</span> bodylingo</a><div className="sidebar-label">YOUR SPACE</div><nav aria-label="Main navigation" className="side-nav">{screens.map(({ name, icon: Icon }) => <button key={name} className={`nav-link ${screen === name ? "active" : ""}`} aria-current={screen === name ? "page" : undefined} onClick={() => setScreen(name)}><Icon size={19} strokeWidth={1.8} /><span>{name}</span>{name === "Learning" && <span className="nav-dot" />}</button>)}</nav><div className="sidebar-bottom"><div className="sidebar-mascot">🐧<div><strong>You’ve got this!</strong><span>Curiosity looks good on you.</span></div></div><button className="user-mini" onClick={() => setScreen("Profile")}><span className="mini-avatar">{user.username.slice(0, 1).toUpperCase()}</span><span><strong>{user.username}</strong><small>My profile</small></span><ChevronRight size={16} /></button></div></aside>
    <main className="main-column"><header className="topbar"><div className="mobile-brand"><span className="brand-mark">b.</span> bodylingo</div><span className="topbar-greeting">A little more understanding, every day <span>✦</span></span><button className="top-avatar" aria-label="Open profile" onClick={() => setScreen("Profile")}>{user.username.slice(0, 1).toUpperCase()}</button></header><div className="content-area" key={`${screen}-${showOnboarding}`}>{showOnboarding ? <OnboardingScreen initial={user.preferences} onSaved={savePreferences} /> : screen === "Learning" ? <LearningScreen onProgress={setProgress} /> : screen === "Scenario" ? <ScenarioScreen /> : screen === "Profile" ? <ProfileScreen user={user} onLogout={onLogout} progress={progress} onEdit={() => { setReturnToProfile(true); setShowOnboarding(true); }} /> : <ComingSoon screen={screen} />}</div></main>
    <nav aria-label="Mobile navigation" className="bottom-nav">{screens.map(({ name, icon: Icon }) => <button key={name} className={screen === name ? "selected" : ""} aria-current={screen === name ? "page" : undefined} onClick={() => setScreen(name)}><Icon size={20} /><span>{name}</span></button>)}</nav>
  </div>;
}

export default function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [onboardingPending, setOnboardingPending] = useState(false);
  useEffect(() => {
    if (!localStorage.getItem("bodylingo_access_token")) {
      setChecking(false);
      return;
    }
    apiRequest<AuthUser>("/api/auth/me")
      .then((currentUser) => {
        setUser(currentUser);
        setOnboardingPending(!currentUser.preferences || Object.keys(currentUser.preferences).length === 0);
      })
      .catch(() => clearAuth())
      .finally(() => setChecking(false));
  }, []);

  async function logout() {
    try { await apiRequest<void>("/api/auth/logout", { method: "POST" }); } catch { /* Local sign-out still works if the API is offline. */ }
    clearAuth();
    setUser(null);
  }

  if (checking) return <div className="app-loading"><span className="loading-dot" /> Opening your space…</div>;
  if (!user) return <AuthScreen onAuthenticated={(authenticated) => {
    setUser(authenticated);
    setOnboardingPending(!authenticated.preferences || Object.keys(authenticated.preferences).length === 0);
  }} />;
  return <AppShell user={user} onUserUpdate={setUser} onboardingPending={onboardingPending} onLogout={logout} />;
}
