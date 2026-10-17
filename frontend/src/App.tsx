import { useEffect, useState, type FormEvent } from "react";
import {
  BookOpen,
  ChevronRight,
  Compass,
  Heart,
  LogOut,
  Menu,
  MessageCircle,
  Mic,
  Moon,
  Search,
  ShieldCheck,
  Sun,
  UsersRound,
  X,
} from "lucide-react";
import { apiRequest, clearAuth, saveAuth, type AuthResult, type AuthUser, type LessonSummary, type LessonDetail, type LearningQuestion, type LearningProgress, type LearningReview, type Preferences, type ScenarioDetail, type ScenarioProgress, type ScenarioResponse, type ScenarioStep, type ScenarioSummary, type ChatConversation, type ChatMessage, type ChatReference, type ForumFeed, type ForumPost } from "./api";

type Screen = "Observations" | "Responses" | "Scenario" | "Chatbot" | "Forum" | "Profile";
const screens: { name: Screen; icon: typeof BookOpen }[] = [
  { name: "Observations", icon: BookOpen },
  { name: "Responses", icon: Heart },
  { name: "Scenario", icon: Compass },
  { name: "Chatbot", icon: MessageCircle },
  { name: "Forum", icon: UsersRound },
];

function PipImage({ className = "", alt = "Pip the penguin" }: { className?: string; alt?: string }) {
  return <img className={`pip-image ${className}`} src="/pip-learning.png" alt={alt} />;
}

function AuthScreen({ onAuthenticated, theme, onToggleTheme }: { onAuthenticated: (user: AuthUser) => void; theme: "light" | "dark"; onToggleTheme: () => void }) {
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
        <a className="brand" href="#home" aria-label="BodyLingo home"><span className="brand-mark">b.</span> BodyLingo</a>
        <button className="icon-button auth-theme-toggle" aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`} onClick={onToggleTheme}>{theme === "light" ? <Moon size={19} /> : <Sun size={19} />}</button>
        <div className="auth-message">
          <PipImage className="mascot-bubble" />
          <p className="eyebrow">BODYLINGO</p>
          <h1>Make room for context.</h1>
          <p className="story-copy">Learn to notice cues, ask with care, and leave space for what you don’t know yet.</p>
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

function ObservationsScreen({ onProgress, initialLessonId }: { onProgress: (progress: LearningProgress) => void; initialLessonId?: string }) {
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

  useEffect(() => { if (initialLessonId) void openLesson(initialLessonId); }, [initialLessonId]);

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
      <PipImage className="lesson-pip pip-motion" alt="Pip reading along" />
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
      <div><p className="eyebrow">OBSERVATIONS</p><h1>Notice the cue. Make room for context.</h1><p>Short lessons for everyday conversations.</p></div>
      <PipImage className="banner-penguin pip-motion" alt="Pip reading a coral journal" />
    </div>
    {progress && <div className="learning-progress"><span><strong>{progress.completed_lessons.length}</strong> lessons completed</span><span><strong>{progress.correct_answers}</strong> correct answers</span><span><strong>{progress.due_reviews}</strong> reviews due</span></div>}
    {reviews.length > 0 && <section className="review-panel"><div><p className="eyebrow">SPACED PRACTICE</p><h2>Questions to revisit</h2><p>Incorrect answers return here on a gentle schedule. Answering a review correctly spaces the next revisit further out.</p></div><div className="review-list">{reviews.map((review) => <button key={`${review.lesson_id}-${review.question.id}`} onClick={() => void openLesson(review.lesson_id, review.question.id)} disabled={!review.is_due} className="review-item"><span>{review.is_due ? "Ready to review" : `Due ${new Date(review.due_at).toLocaleDateString()}`}</span><strong>{review.lesson_title}</strong><small>{review.question.prompt}</small></button>)}</div></section>}
    <div className="section-heading"><div><p className="eyebrow">LESSONS</p><h2>Choose a topic</h2></div></div>
    {error && <p className="inline-error" role="alert">{error}</p>}
    {recommendationError && <p className="inline-error" role="alert">{recommendationError}</p>}
    <div className="lesson-grid">
      {lessons.map((lesson, index) => <article className={`lesson-card lesson-tone-${index % 4} ${lesson.locked ? "locked" : ""}`} key={lesson.id}>
        <div className="lesson-card-top"><span className="lesson-icon"><BookOpen size={20} /></span><span className="lesson-duration">{lesson.estimated_duration_minutes} min</span></div>
        <p className="lesson-topic">{lesson.topic}{lesson.is_premium ? " · PREMIUM" : ""}</p><h3>{lesson.title}</h3><p className="lesson-description">{lesson.description}</p><small className="recommendation-reason">{lesson.recommendation_reason}</small>
        <div className="lesson-card-bottom">{lesson.completed && <span className="difficulty">Completed</span>}<button aria-label={`${lesson.locked ? "Locked" : "Open"} ${lesson.title}`} className="round-arrow" disabled={lesson.locked || busy} onClick={() => void openLesson(lesson.id)}>{lesson.locked ? <ShieldCheck size={16} /> : <ChevronRight size={18} />}</button></div>
      </article>)}
    </div>
    {!lessons.length && !error && <div className="loading-card"><span className="loading-dot" /> Finding your first lessons…</div>}
  </>;
}

const responsePractices = [
  {
    id: "grounding",
    title: "When everything feels overwhelming",
    method: "Grounding",
    summary: "Bring attention back to what is happening around you, one sense at a time.",
    steps: ["Notice where you are and what you are doing.", "Name a few things you can see, hear, and feel against your body.", "Let your attention move gently between those details and the next small thing you need to do."],
    source: "WHO stress guide",
    url: "https://www.who.int/publications/b/53604",
  },
  {
    id: "breathing",
    title: "When your body feels tense",
    method: "Gentle breathing",
    summary: "Try a few minutes of steady, comfortable breathing. There is no need to take a very deep breath.",
    steps: ["Settle into a comfortable position, if you can.", "Breathe in gently through your nose and out through your mouth, without forcing it.", "If counting feels comfortable, count slowly to five on the inhale and again on the exhale. Stop or return to normal breathing if this feels uncomfortable."],
    source: "NHS breathing exercise",
    url: "https://www.nhs.uk/mental-health/self-help/guides-tools-and-activities/breathing-exercises-for-stress/",
  },
  {
    id: "unhooking",
    title: "When a thought keeps looping",
    method: "Notice and name",
    summary: "Make a little space around a thought instead of treating it as a fact or trying to force it away.",
    steps: ["Notice the thought that keeps returning.", "Try phrasing it as: “I’m noticing the thought that …”", "Bring your attention back to the present, then choose one small action that matters to you."],
    source: "WHO stress guide",
    url: "https://www.who.int/publications/b/53604",
  },
  {
    id: "small-step",
    title: "When starting feels difficult",
    method: "One values-led step",
    summary: "Choose a small action connected to what matters to you; it does not need to change your whole day.",
    steps: ["Name one thing that matters to you right now, such as rest, connection, or care.", "Pick a step that could take a few minutes: drink water, open a window, or send a simple message.", "Do the step at your own pace, and notice what you need next."],
    source: "WHO stress guide",
    url: "https://www.who.int/publications/b/53604",
  },
];

function ResponsesScreen() {
  return <section className="responses-layout">
    <div className="welcome-banner responses-hero">
      <div><p className="eyebrow">RESPONSES</p><h1>A small step can help.</h1><p>Choose a practice that feels manageable.</p></div>
      <PipImage className="banner-penguin pip-motion" alt="Pip with a learning journal" />
    </div>
    <div className="responses-note"><ShieldCheck size={18} /><p>These self-guided practices are educational, not diagnosis or treatment. They may not fit everyone.</p></div>
    <div className="response-grid">{responsePractices.map((practice) => <details className="response-card" key={practice.id}>
      <summary><span className="response-method">{practice.method}</span><h2>{practice.title}</h2><p>{practice.summary}</p><span className="response-open">View steps <ChevronRight size={16} /></span></summary>
      <ol>{practice.steps.map((step) => <li key={step}>{step}</li>)}</ol>
      <a className="response-source" href={practice.url} target="_blank" rel="noreferrer">Source: {practice.source}<ChevronRight size={14} /></a>
    </details>)}</div>
    <p className="responses-help">If you may hurt yourself or someone else, or cannot stay safe, contact your local emergency service or crisis support and reach out to someone you trust.</p>
  </section>;
}

function ScenarioScreen({ initialScenarioId }: { initialScenarioId?: string }) {
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

  useEffect(() => {
    if (!initialScenarioId) return;
    void apiRequest<ScenarioDetail>(`/api/scenarios/${initialScenarioId}`).then((detail) => {
      setActive(detail); setStep(detail); setFeedback(null); setIsComplete(false);
    }).catch((cause) => setError(cause instanceof Error ? cause.message : "This scenario could not be opened."));
  }, [initialScenarioId]);

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
    {feedback && <article className={`scenario-feedback ${isComplete ? "finished" : ""}`} role="status"><PipImage className="scenario-feedback-mascot pip-motion" alt="Pip considering the outcome" /><div><strong>{isComplete ? "Scenario complete" : "A possible outcome"}</strong><p>{feedback}</p>{isComplete ? <button className="button button-primary" onClick={() => { setActive(null); setStep(null); setFeedback(null); }}>Back to scenarios</button> : <button className="button button-primary" onClick={() => setFeedback(null)}>Continue<ChevronRight size={16} /></button>}</div></article>}
    {error && <p className="inline-error" role="alert">{error}</p>}
  </section>;

  return <section className="scenario-library"><div className="scenario-hero"><p className="eyebrow">SCENARIOS</p><h1>Practice a conversation.</h1><p>Try a response. See where it might lead.</p><PipImage className="scenario-hero-pip pip-motion" alt="Pip exploring a conversation" /></div>
    {error && <p className="inline-error" role="alert">{error}</p>}
    <div className="section-heading"><div><p className="eyebrow">BRANCHING PRACTICE</p><h2>Choose a scenario</h2></div><span className="recommendation-label">Progress is saved to your account</span></div>
    <div className="scenario-grid">{scenarios.map((scenario, index) => <article className={`scenario-card scenario-tone-${index % 4}`} key={scenario.id}><div className="scenario-card-icon"><Compass size={20} /></div><p className="scenario-topic">EVERYDAY PRACTICE</p><h2>{scenario.title}</h2><p>{scenario.description}</p><ul>{scenario.learning_objectives.slice(0, 2).map((objective) => <li key={objective}>{objective}</li>)}</ul><span className="scenario-asset-note">{scenario.media_placeholder}</span><button className="button button-primary" disabled={busy} onClick={() => void startScenario(scenario)}>{completed.includes(scenario.id) ? "Practise again" : "Start scenario"}<ChevronRight size={16} /></button></article>)}</div>
    {!scenarios.length && !error && <div className="loading-card"><span className="loading-dot" /> Loading scenarios…</div>}
  </section>;
}

function ChatScreen({ onOpenReference }: { onOpenReference: (reference: ChatReference) => void }) {
  const [conversations, setConversations] = useState<ChatConversation[]>([]);
  const [activeId, setActiveId] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [voiceAvailable, setVoiceAvailable] = useState(false);

  async function loadConversation(id: string) {
    const conversation = await apiRequest<ChatConversation>(`/api/chat/conversations/${id}`);
    setActiveId(id);
    setMessages(conversation.messages);
  }
  async function refresh() {
    const items = await apiRequest<ChatConversation[]>("/api/chat/conversations");
    setConversations(items);
    if (items.length && !activeId) await loadConversation(items[0].id);
  }
  useEffect(() => {
    setVoiceAvailable("SpeechRecognition" in window || "webkitSpeechRecognition" in window);
    void refresh().catch((cause) => setError(cause instanceof Error ? cause.message : "Chat history could not be loaded."));
  }, []);

  async function newConversation() {
    setBusy(true); setError("");
    try {
      const created = await apiRequest<ChatConversation>("/api/chat/conversations", { method: "POST" });
      setConversations((items) => [created, ...items]); setActiveId(created.id); setMessages([]);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "A conversation could not be started."); }
    finally { setBusy(false); }
  }
  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const content = draft.trim();
    if (!content || busy) return;
    setBusy(true); setError("");
    try {
      let id = activeId;
      if (!id) {
        const created = await apiRequest<ChatConversation>("/api/chat/conversations", { method: "POST" });
        id = created.id; setActiveId(id);
      }
      const reply = await apiRequest<ChatMessage>(`/api/chat/conversations/${id}/messages`, { method: "POST", body: JSON.stringify({ content }) });
      setMessages((items) => [...items, { id: `pending-${Date.now()}`, role: "user", content, references: [], created_at: new Date().toISOString() }, reply]);
      setDraft(""); await refresh();
    } catch (cause) { setError(cause instanceof Error ? cause.message : "Your message could not be sent."); }
    finally { setBusy(false); }
  }
  function dictate() {
    const Speech = (window as Window & { SpeechRecognition?: new () => { lang: string; onresult: (event: { results: { [index: number]: { [index: number]: { transcript: string } } } }) => void; onerror: () => void; start: () => void }; webkitSpeechRecognition?: new () => { lang: string; onresult: (event: { results: { [index: number]: { [index: number]: { transcript: string } } } }) => void; onerror: () => void; start: () => void } }).SpeechRecognition ?? (window as Window & { webkitSpeechRecognition?: new () => { lang: string; onresult: (event: { results: { [index: number]: { [index: number]: { transcript: string } } } }) => void; onerror: () => void; start: () => void } }).webkitSpeechRecognition;
    if (!Speech) return;
    const recognition = new Speech(); recognition.lang = navigator.language;
    recognition.onresult = (event) => setDraft((text) => `${text}${text ? " " : ""}${event.results[0][0].transcript}`);
    recognition.onerror = () => setError("Voice input was unavailable. You can type your message instead."); recognition.start();
  }
  return <section className="chat-layout"><header className="chat-heading"><div><p className="eyebrow">CHAT</p><h1>Ask Pip</h1><p>Ask about a moment. Explore it together.</p></div><button className="button button-primary" onClick={() => void newConversation()} disabled={busy}>New conversation</button></header>
    <div className="chat-workspace"><aside className="chat-history"><h2>Your conversations</h2>{conversations.map((item) => <button key={item.id} className={activeId === item.id ? "selected" : ""} onClick={() => void loadConversation(item.id)}>{item.title}</button>)}{!conversations.length && <p>New chats will appear here.</p>}</aside>
      <div className="chat-panel"><div className="chat-messages" aria-live="polite">{messages.length === 0 ? <div className="chat-welcome"><PipImage className="chat-pip" alt="Pip, your conversation companion" /><h2>Ask Pip</h2><p>What’s on your mind?</p><div className="chat-suggestions">{["Ask for clarification", "Check in with a quiet teammate"] .map((question) => <button key={question} onClick={() => setDraft(question)}>{question}</button>)}</div></div> : messages.map((message) => <article className={`chat-message ${message.role}`} key={message.id}>{message.role === "assistant" && <PipImage className="chat-message-pip" alt="Pip" />}<p>{message.content}</p>{message.references.length > 0 && <div className="chat-references"><span>Related practice</span>{message.references.map((reference) => <button key={`${reference.type}-${reference.id}`} onClick={() => onOpenReference(reference)}>{reference.type === "lesson" ? <BookOpen size={15} /> : <Compass size={15} />}{reference.title}<ChevronRight size={14} /></button>)}</div>}</article>)}</div>
        {error && <p className="inline-error" role="alert">{error}</p>}<form className="chat-compose" onSubmit={(event) => void send(event)}><textarea aria-label="Message Pip" maxLength={2000} placeholder="Write a message…" value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); event.currentTarget.form?.requestSubmit(); } }} />{voiceAvailable && <button type="button" className="button button-quiet voice-button" onClick={dictate} aria-label="Use voice input"><Mic size={20} /></button>}<button className="button button-primary" disabled={busy || !draft.trim()}>{busy ? "Thinking…" : "Send"}<ChevronRight size={16} /></button></form><small className="chat-privacy">Avoid sharing sensitive personal information.</small></div></div></section>;
}

function ForumScreen() {
  const [posts, setPosts] = useState<ForumPost[]>([]);
  const [categories, setCategories] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("");
  const [classification, setClassification] = useState<ForumFeed["classification"]>("deterministic_fallback");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let current = true;
    const timer = window.setTimeout(() => {
      const params = new URLSearchParams();
      if (query.trim()) params.set("query", query.trim());
      if (category) params.set("category", category);
      setLoading(true);
      apiRequest<ForumFeed>(`/api/forum/posts?${params.toString()}`)
        .then((feed) => { if (!current) return; setPosts(feed.posts); setCategories(feed.categories); setClassification(feed.classification); setError(""); })
        .catch((cause) => { if (current) setError(cause instanceof Error ? cause.message : "The community feed is unavailable."); })
        .finally(() => { if (current) setLoading(false); });
    }, 180);
    return () => { current = false; window.clearTimeout(timer); };
  }, [query, category]);

  return <section className="forum-layout"><header className="forum-hero"><div><p className="eyebrow">COMMUNITY</p><h1>Learn from each other.</h1><p>Short reflections on everyday communication.</p></div><PipImage className="forum-illustration" alt="Pip" /></header>
    <div className="forum-sample-note"><ShieldCheck size={16} /><span>These are fictional sample posts for the demo. This forum is read-only.</span></div>
    <div className="forum-controls"><label className="forum-search"><Search size={18} /><input aria-label="Search forum posts" type="search" placeholder="Search topics, phrases, or situations…" value={query} onChange={(event) => setQuery(event.target.value)} /></label><div className="forum-filter-label"><span>Browse by topic</span><small>{classification === "groq" ? "AI-assisted tags" : "Topic tags"}</small></div><div className="forum-categories"><button className={!category ? "selected" : ""} onClick={() => setCategory("")}>All topics</button>{categories.map((item) => <button key={item} className={category === item ? "selected" : ""} onClick={() => setCategory(category === item ? "" : item)}>{item}</button>)}</div></div>
    {error && <p className="inline-error" role="alert">{error}</p>}
    <div className="forum-feed" aria-live="polite">{posts.map((post) => <article className="forum-post" key={post.id}><div className="forum-post-meta"><span className="forum-category">{post.category}</span><span>{new Date(post.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" })}</span></div><h2>{post.title}</h2><p className="forum-excerpt">{post.excerpt}</p><div className="forum-post-footer"><span className="forum-author"><span className="forum-avatar">{post.author_display_name.slice(0, 1)}</span> {post.author_display_name} <small>· fictional</small></span><div className="forum-tags">{post.topic_tags.map((tag) => <span key={tag}>{tag}</span>)}</div></div></article>)}
      {loading && <div className="loading-card"><span className="loading-dot" /> Finding conversations…</div>}
      {!loading && !error && !posts.length && <div className="forum-empty"><span aria-hidden="true">🔎</span><h2>No posts found</h2><p>Try a different phrase or choose another topic.</p><button className="text-button" onClick={() => { setQuery(""); setCategory(""); }}>Clear filters</button></div>}
    </div>
  </section>;
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

  return <section className="onboarding-layout"><div className="onboarding-heading"><PipImage className="onboarding-penguin" alt="Pip with a learning journal" /><p className="eyebrow">YOUR PREFERENCES</p><h1>What would you like to explore?</h1><p>Pick topics and situations that feel useful. You can change these choices later.</p></div>
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

function ProfileScreen({ user, onLogout, onEdit, onLearning, onScenarios, progress }: { user: AuthUser; onLogout: () => void; onEdit: () => void; onLearning: () => void; onScenarios: () => void; progress: LearningProgress | null }) {
  const preferences = user.preferences;
  const [scenarioProgress, setScenarioProgress] = useState<ScenarioProgress | null>(null);
  const [lessons, setLessons] = useState<LessonSummary[]>([]);
  const [profileProgress, setProfileProgress] = useState<LearningProgress | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  useEffect(() => {
    let mounted = true;
    Promise.all([
      apiRequest<ScenarioProgress>("/api/scenarios/progress"),
      apiRequest<LessonSummary[]>("/api/learning/recommendations"),
      apiRequest<LearningProgress>("/api/learning/progress"),
    ]).then(([scenarios, catalog, currentProgress]) => {
      if (!mounted) return;
      setScenarioProgress(scenarios);
      setLessons(catalog);
      setProfileProgress(currentProgress);
    }).catch((cause) => {
      if (mounted) setError(cause instanceof Error ? cause.message : "Some profile details could not be loaded.");
    }).finally(() => { if (mounted) setLoading(false); });
    return () => { mounted = false; };
  }, []);
  const lessonTitles = new Map(lessons.map((lesson) => [lesson.id, lesson.title]));
  const currentProgress = profileProgress ?? progress;
  const completedLessons = currentProgress?.completed_lessons ?? [];
  const lockedLessons = lessons.filter((lesson) => lesson.locked);
  return <section className="profile-layout"><div className="profile-title"><p className="eyebrow">YOUR SPACE</p><h1>Profile & preferences</h1><p>Make this learning experience feel like yours.</p></div><article className="profile-card"><div className="profile-avatar">{user.username.slice(0, 1).toUpperCase()}</div><div className="profile-identity"><h2>{user.username}</h2><p>{user.email}</p></div><span className="profile-badge"><ShieldCheck size={15} /> Account</span></article>
    <article className="preferences-card"><div className="preferences-icon"><Heart size={19} /></div><div className="preferences-content"><h3>Your learning preferences</h3><p><strong>Topics</strong>{preferences?.topics?.length ? preferences.topics.join(" · ") : "Not selected"}</p><p><strong>Situations</strong>{preferences?.situations?.length ? preferences.situations.join(" · ") : "Not selected"}</p><p><strong>Explanation style</strong>{preferences?.explanation_style ?? "balanced"}</p><p><strong>Communication preferences</strong>{preferences?.communication_preferences?.length ? preferences.communication_preferences.join(" · ") : "Not selected"}</p><p><strong>Cultural contexts</strong>{preferences?.cultural_contexts?.length ? preferences.cultural_contexts.join(" · ") : "Not selected"}</p><button className="text-button profile-edit" onClick={onEdit}>Edit preferences</button></div></article>
    {error && <p className="inline-error" role="alert">{error}</p>}
    <article className="profile-progress"><div className="profile-section-heading"><h3>Learning progress</h3><button className="text-button" onClick={onLearning}>Open learning</button></div><div><span>{currentProgress?.completed_lessons.length ?? "—"}<small>completed lessons</small></span><span>{currentProgress?.correct_answers ?? "—"}<small>correct answers</small></span><span>{currentProgress?.due_reviews ?? "—"}<small>reviews due</small></span></div>
      <h4>Completed lessons</h4>{completedLessons.length ? <ul className="profile-resource-list">{completedLessons.map((id) => <li key={id}>{lessonTitles.get(id) ?? id}</li>)}</ul> : <p>{loading ? "Loading lesson progress…" : "No completed lessons yet. Your learning progress will appear here."}</p>}
      {Boolean(currentProgress?.due_reviews) && <button className="button button-quiet profile-action" onClick={onLearning}>Review {currentProgress?.due_reviews} {currentProgress?.due_reviews === 1 ? "question" : "questions"} due</button>}
    </article>
    <article className="profile-progress scenario-history"><div className="profile-section-heading"><h3>Scenario practice</h3><button className="text-button" onClick={onScenarios}>Open scenarios</button></div><p>{scenarioProgress?.completed_scenarios.length ?? (loading ? "—" : 0)} scenarios completed</p>{scenarioProgress?.sessions.length ? <ul className="scenario-history-list">{scenarioProgress.sessions.slice(0, 5).map((session, index) => <li key={`${session.scenario_id}-${session.started_at}-${index}`}><span><strong>{session.title}</strong><small>{session.response_count} {session.response_count === 1 ? "choice" : "choices"} · Started {new Date(session.started_at).toLocaleDateString()}</small></span><span className={`history-status ${session.is_completed ? "complete" : "in-progress"}`}>{session.is_completed ? "Completed" : "In progress"}</span></li>)}</ul> : <p>{loading ? "Loading scenario history…" : "Scenario sessions you start will be saved here."}</p>}</article>
    <article className="profile-progress entitlement-card"><div className="profile-section-heading"><h3>Learning access</h3><span className={`entitlement-badge ${user.is_premium ? "premium" : "free"}`}>{user.is_premium ? "Premium" : "Free"}</span></div><p>{user.is_premium ? "Demo premium access is enabled for this account." : "You have access to free lessons. No payment has been processed."}</p>{lockedLessons.length > 0 && <><h4>Advanced lessons</h4><ul className="profile-resource-list locked-list">{lockedLessons.map((lesson) => <li key={lesson.id}><ShieldCheck size={14} /> {lesson.title}</li>)}</ul><button className="text-button" onClick={onLearning}>View lesson catalog</button></>}</article>
    <button className="button button-quiet logout-button" onClick={onLogout}><LogOut size={17} /> Sign out</button></section>;
}

function AppShell({ user, onUserUpdate, onLogout, onboardingPending, theme, onToggleTheme }: { user: AuthUser; onUserUpdate: (user: AuthUser) => void; onLogout: () => void; onboardingPending: boolean; theme: "light" | "dark"; onToggleTheme: () => void }) {
  const [screen, setScreen] = useState<Screen>("Observations");
  const [showOnboarding, setShowOnboarding] = useState(onboardingPending);
  const [returnToProfile, setReturnToProfile] = useState(false);
  const [progress, setProgress] = useState<LearningProgress | null>(null);
  const [pendingReference, setPendingReference] = useState<ChatReference | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  async function savePreferences(preferences: Preferences) {
    const saved = await apiRequest<Preferences>("/api/learning/preferences", { method: "PUT", body: JSON.stringify(preferences) });
    onUserUpdate({ ...user, preferences: saved });
    setShowOnboarding(false);
    setScreen(returnToProfile ? "Profile" : "Observations");
    setReturnToProfile(false);
  }

  return <div className={`app-shell ${sidebarOpen ? "sidebar-open" : ""}`}>
    <a className="skip-link" href="#main-content">Skip to main content</a>
    {sidebarOpen && <button className="sidebar-scrim" aria-label="Close navigation" onClick={() => setSidebarOpen(false)} />}
    <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}><div className="sidebar-top"><a className="brand" href="#home"><span className="brand-mark">b.</span> BodyLingo</a><button className="icon-button sidebar-close" aria-label="Close navigation" onClick={() => setSidebarOpen(false)}><X size={20} /></button></div><div className="sidebar-label">NAVIGATION</div><nav aria-label="Main navigation" className="side-nav">{screens.map(({ name, icon: Icon }) => <button key={name} className={`nav-link ${screen === name ? "active" : ""}`} aria-current={screen === name ? "page" : undefined} onClick={() => { setScreen(name); setSidebarOpen(false); }}><Icon size={19} strokeWidth={1.8} /><span>{name}</span></button>)}</nav><div className="sidebar-bottom"><button className="user-mini" onClick={() => { setScreen("Profile"); setSidebarOpen(false); }}><span className="mini-avatar">{user.username.slice(0, 1).toUpperCase()}</span><span><strong>{user.username}</strong><small>Profile</small></span><ChevronRight size={16} /></button></div></aside>
    <main className="main-column" id="main-content" tabIndex={-1}><header className="topbar"><button className="icon-button sidebar-toggle" aria-label={sidebarOpen ? "Close navigation" : "Open navigation"} aria-expanded={sidebarOpen} onClick={() => setSidebarOpen((open) => !open)}>{sidebarOpen ? <X size={21} /> : <Menu size={21} />}</button><div className="mobile-brand"><span className="brand-mark">b.</span> BodyLingo</div><div className="topbar-actions"><button className="icon-button theme-toggle" aria-label={`Switch to ${theme === "light" ? "dark" : "light"} mode`} onClick={onToggleTheme}>{theme === "light" ? <Moon size={19} /> : <Sun size={19} />}</button><button className="top-avatar" aria-label="Open profile" onClick={() => setScreen("Profile")}>{user.username.slice(0, 1).toUpperCase()}</button></div></header><div className="content-area" key={`${screen}-${showOnboarding}`}>{showOnboarding ? <OnboardingScreen initial={user.preferences} onSaved={savePreferences} /> : screen === "Observations" ? <ObservationsScreen onProgress={setProgress} initialLessonId={pendingReference?.type === "lesson" ? pendingReference.id : undefined} /> : screen === "Responses" ? <ResponsesScreen /> : screen === "Scenario" ? <ScenarioScreen initialScenarioId={pendingReference?.type === "scenario" ? pendingReference.id : undefined} /> : screen === "Chatbot" ? <ChatScreen onOpenReference={(reference) => { setPendingReference(reference); setScreen(reference.type === "lesson" ? "Observations" : "Scenario"); }} /> : screen === "Forum" ? <ForumScreen /> : <ProfileScreen user={user} onLogout={onLogout} progress={progress} onEdit={() => { setReturnToProfile(true); setShowOnboarding(true); }} onLearning={() => setScreen("Observations")} onScenarios={() => setScreen("Scenario")} />}</div></main>
    <nav aria-label="Mobile navigation" className="bottom-nav">{screens.map(({ name, icon: Icon }) => <button key={name} className={screen === name ? "selected" : ""} aria-current={screen === name ? "page" : undefined} onClick={() => setScreen(name)}><Icon size={20} /><span>{name}</span></button>)}</nav>
  </div>;
}

export default function App() {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checking, setChecking] = useState(true);
  const [onboardingPending, setOnboardingPending] = useState(false);
  const [theme, setTheme] = useState<"light" | "dark">(() => localStorage.getItem("bodylingo_theme") === "dark" ? "dark" : "light");
  const toggleTheme = () => setTheme((current) => current === "light" ? "dark" : "light");
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("bodylingo_theme", theme);
  }, [theme]);
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
  if (!user) return <AuthScreen theme={theme} onToggleTheme={toggleTheme} onAuthenticated={(authenticated) => {
    setUser(authenticated);
    setOnboardingPending(!authenticated.preferences || Object.keys(authenticated.preferences).length === 0);
  }} />;
  return <AppShell user={user} onUserUpdate={setUser} onboardingPending={onboardingPending} onLogout={logout} theme={theme} onToggleTheme={toggleTheme} />;
}
