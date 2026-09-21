import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type FormEvent,
} from "react";
import {
  ArrowLeft,
  ArrowUpRight,
  BriefcaseBusiness,
  Check,
  ChevronRight,
  FileText,
  LogOut,
  Plus,
  Search,
  SlidersHorizontal,
  Sparkles,
  UploadCloud,
} from "lucide-react";
import { api, ApiError, mutation, setCsrf } from "./api";
import {
  Empty,
  ErrorMessage,
  Score,
  StageBadge,
  stageLabel,
} from "./components";
import { CandidatePanel } from "./CandidatePanel";
import { Compare } from "./Compare";
import { JobEditor } from "./JobEditor";
import { Upload } from "./Upload";
import type { Candidate, Job, Page, Session } from "./types";
export default function App() {
  const [session, setSession] = useState<Session | null>(null);
  const [initialError, setInitialError] = useState("");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [jobId, setJobId] = useState<number | null>(null);
  const [editor, setEditor] = useState<false | "new" | Job>(false);
  const [view, setView] = useState<"roles" | "compare">("roles");
  const [uploading, setUploading] = useState(false);
  const [reviewOrder, setReviewOrder] = useState<number[]>([]);
  const [candidateId, setCandidateId] = useState<number | null>(null);
  const [page, setPage] = useState<Page<Candidate> | null>(null);
  const [search, setSearch] = useState("");
  const [stage, setStage] = useState("");
  const [evaluation, setEvaluation] = useState("");
  const [minScore, setMinScore] = useState("");
  const [ordering, setOrdering] = useState("score");
  const [pageNumber, setPageNumber] = useState(1);
  const [selected, setSelected] = useState<number[]>([]);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(false);
  const requestVersion = useRef(0);
  const job = jobs.find((j) => j.id === jobId);
  const loadJobs = useCallback(
    async () => setJobs(await api<Job[]>("jobs/")),
    [],
  );
  const loadCandidates = useCallback(async () => {
    if (!jobId) return;
    const version = ++requestVersion.current;
    const query = new URLSearchParams({
      job: String(jobId),
      search,
      stage,
      evaluation,
      min_score: minScore,
      ordering,
      page: String(pageNumber),
    });
    try {
      const result = await api<Page<Candidate>>(`applications/?${query}`);
      if (version === requestVersion.current) setPage(result);
    } catch (error) {
      if (error instanceof ApiError && error.status === 404 && pageNumber > 1) {
        if (version === requestVersion.current) setPageNumber(1);
        return;
      }
      throw error;
    }
  }, [jobId, search, stage, evaluation, minScore, ordering, pageNumber]);
  const refresh = useCallback(() => {
    void Promise.all([loadJobs(), loadCandidates()]).catch((e) =>
      setError(e.message),
    );
  }, [loadJobs, loadCandidates]);
  useEffect(() => {
    api<Session>("session/")
      .then((s) => {
        setSession(s);
        setCsrf(s.csrf_token);
      })
      .catch((e) => setInitialError(e.message));
  }, []);
  useEffect(() => {
    if (session?.user) void loadJobs().catch((e) => setError(e.message));
  }, [session?.user, loadJobs]);
  useEffect(() => {
    if (!session?.user || !jobId) return;
    setLoading(true);
    setSelected([]);
    const timer = setTimeout(() => {
      void loadCandidates()
        .catch((e) => setError(e.message))
        .finally(() => setLoading(false));
    }, 180);
    return () => {
      clearTimeout(timer);
      requestVersion.current++;
    };
  }, [session?.user, jobId, loadCandidates]);
  useEffect(() => {
    if (!session?.user || !jobId) return;
    const timer = setInterval(refresh, 4000);
    return () => clearInterval(timer);
  }, [session?.user, jobId, refresh]);
  function openJob(id: number | null) {
    setJobId(id);
    setSearch("");
    setStage("");
    setEvaluation("");
    setMinScore("");
    setPageNumber(1);
    setPage(null);
    setSelected([]);
    setNotice("");
    setError("");
  }
  async function evaluate() {
    if (!job) return;
    setBusy(true);
    setError("");
    try {
      const result = await mutation<{ queued: number }>(
        `jobs/${job.id}/evaluate/`,
        selected.length ? { application_ids: selected } : {},
      );
      setNotice(
        result.queued
          ? `${result.queued} candidate${result.queued === 1 ? "" : "s"} queued for evaluation. Results will appear as they finish.`
          : "All selected candidates already have a current evaluation or are in the queue.",
      );
      refresh();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function bulkShortlist() {
    setBusy(true);
    setError("");
    try {
      for (const id of selected)
        await mutation(
          `applications/${id}/`,
          { stage: "shortlisted" },
          "PATCH",
        );
      setNotice(`${selected.length} candidates shortlisted.`);
      setSelected([]);
      refresh();
    } catch (e) {
      setError((e as Error).message);
      refresh();
    } finally {
      setBusy(false);
    }
  }
  async function logout() {
    try {
      await api("session/", { method: "DELETE" });
      const s = await api<Session>("session/");
      setSession(s);
      setCsrf(s.csrf_token);
      setJobs([]);
      openJob(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  if (!session)
    return (
      <main className="startup">
        <h1>HireLens</h1>
        {initialError ? (
          <ErrorMessage
            message={`Couldn't connect to the application. ${initialError}`}
          />
        ) : (
          <p>Opening your workspace…</p>
        )}
      </main>
    );
  if (!session.user)
    return (
      <Login
        session={session}
        onLogin={(s) => {
          setSession(s);
          setCsrf(s.csrf_token);
        }}
      />
    );
  const candidateIndex = reviewOrder.indexOf(candidateId ?? -1);
  function reviewCandidate(id: number) {
    setReviewOrder(page?.results.map((c) => c.id) ?? []);
    setCandidateId(id);
  }
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a
          href="#"
          className="brand"
          onClick={(e) => {
            e.preventDefault();
            openJob(null);
          }}
        >
          <span className="brand-mark">
            j<span>j</span>
          </span>
          <span>
            HireLens<small>RECRUITING WORKSPACE</small>
          </span>
        </a>
        <p className="nav-label">WORKSPACE</p>
        <button
          className={`nav-item ${view === "roles" ? "active" : ""}`}
          onClick={() => {
            setView("roles");
            openJob(null);
          }}
        >
          <BriefcaseBusiness size={18} />
          Roles<span>{jobs.length}</span>
        </button>
        <button
          className={`nav-item ${view === "compare" ? "active" : ""}`}
          onClick={() => {
            setView("compare");
            openJob(null);
          }}
        >
          <FileText size={18} />
          Compare
        </button>
        <button
          className="icon-button mobile-only"
          aria-label="Sign out"
          onClick={() => void logout()}
        >
          <LogOut size={16} />
        </button>
        <div className="sidebar-bottom">
          <div className="workspace-note">
            <span className="dot" />A little clarity in hiring.
            <p>Good people. Thoughtful decisions.</p>
          </div>
          <div className="account">
            <div className="avatar">
              {session.user.slice(0, 2).toUpperCase()}
            </div>
            <span>
              {session.user}
              <small>Personal workspace</small>
            </span>
            <button
              className="icon-button"
              aria-label="Sign out"
              onClick={() => void logout()}
            >
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>
      <main className="main">
        <header className="topbar">
          <span>
            Workspace <ChevronRight size={13} />{" "}
            {job ? (
              <>
                <button className="text-button" onClick={() => openJob(null)}>
                  Roles
                </button>
                <ChevronRight size={13} />
                {job.title}
              </>
            ) : (
              "Roles"
            )}
          </span>
          <span className="provider-label">
            <span className="dot" />
            {session.mode === "demo" ? "Demo workspace" : "Powered by Jev"}
          </span>
        </header>
        <div className="content">
          {session.mode === "demo" && (
            <div className="demo-banner">
              Demo mode · Scores are illustrative keyword matches, not live Jev
              evaluations.
            </div>
          )}
          {!session.jev_configured && session.mode !== "demo" && (
            <div className="notice">
              Jev is not connected yet. You can prepare roles and resumes; add
              JEV_API_KEY to the server to enable scoring.
            </div>
          )}
          <ErrorMessage message={error} />
          {notice && (
            <div className="success" role="status">
              {notice}
              <button className="text-button" onClick={() => setNotice("")}>
                Dismiss
              </button>
            </div>
          )}
          {view === "compare" ? (
            <Compare />
          ) : !job ? (
            <>
              <div className="page-heading">
                <div>
                  <p className="eyebrow">A MORE CONSIDERED SHORTLIST</p>
                  <h1>Your roles</h1>
                  <p className="muted">
                    From a pile of resumes to the people worth a conversation.
                  </p>
                </div>
                <button className="primary" onClick={() => setEditor("new")}>
                  <Plus size={17} />
                  Create role
                </button>
              </div>
              <div className="stats">
                <div>
                  <span>Open roles</span>
                  <strong>
                    {jobs.filter((j) => j.status === "open").length}
                  </strong>
                </div>
                <div>
                  <span>Candidates</span>
                  <strong>
                    {jobs.reduce((s, j) => s + j.candidate_count, 0)}
                  </strong>
                </div>
                <div>
                  <span>Shortlisted</span>
                  <strong>
                    {jobs.reduce((s, j) => s + j.shortlisted_count, 0)}
                  </strong>
                </div>
              </div>
              <div className="section-title">
                <h2>
                  All roles <span className="count">{jobs.length}</span>
                </h2>
                <span className="small muted">
                  Your next great hire starts here
                </span>
              </div>
              {jobs.length ? (
                <div className="job-grid">
                  {jobs.map((j) => (
                    <button
                      className="job-card"
                      key={j.id}
                      onClick={() => openJob(j.id)}
                    >
                      <div className="row between">
                        <span
                          className={`badge ${j.status === "open" ? "green" : ""}`}
                        >
                          {j.status === "open" ? "Open role" : "Closed"}
                        </span>
                        <ArrowUpRight size={19} />
                      </div>
                      <h2>{j.title}</h2>
                      <p className="muted">
                        {[j.department, j.location]
                          .filter(Boolean)
                          .join(" · ") || "Location flexible"}
                      </p>
                      <div className="job-card-footer">
                        <span>
                          <strong>{j.candidate_count}</strong> candidates
                        </span>
                        <span>
                          <strong>{j.shortlisted_count}</strong> shortlisted
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <Empty title="Make room for your next great hire.">
                  <p>
                    Create a role, define what matters, and add your first
                    resumes.
                  </p>
                  <button className="primary" onClick={() => setEditor("new")}>
                    <Plus size={16} />
                    Create your first role
                  </button>
                </Empty>
              )}
              <div className="how-it-works">
                <div>
                  <span>01</span>
                  <strong>Define what matters</strong>
                  <p>A clear role and a few thoughtful criteria.</p>
                </div>
                <div>
                  <span>02</span>
                  <strong>Find the relevant experience</strong>
                  <p>One consistent rubric across every resume.</p>
                </div>
                <div>
                  <span>03</span>
                  <strong>Start a conversation</strong>
                  <p>Review the evidence. Build your shortlist.</p>
                </div>
              </div>
            </>
          ) : (
            <>
              <button
                className="back text-button"
                onClick={() => openJob(null)}
              >
                <ArrowLeft size={15} />
                All roles
              </button>
              <div className="page-heading">
                <div>
                  <div className="row">
                    <span
                      className={`badge ${job.status === "open" ? "green" : ""}`}
                    >
                      {job.status === "open" ? "Open role" : "Closed"}
                    </span>
                    <span className="small muted">Criteria v{job.version}</span>
                  </div>
                  <h1>{job.title}</h1>
                  <p className="muted">
                    {[job.department, job.location].filter(Boolean).join(" · ")}
                  </p>
                </div>
                <div className="row">
                  <button className="secondary" onClick={() => setEditor(job)}>
                    <SlidersHorizontal size={16} />
                    Role & criteria
                  </button>
                  <button
                    className="primary"
                    disabled={job.status === "closed"}
                    onClick={() => setUploading(true)}
                  >
                    <Plus size={17} />
                    Add resumes
                  </button>
                </div>
              </div>
              <div className="stats">
                <div>
                  <span>Candidates</span>
                  <strong>{job.candidate_count}</strong>
                </div>
                <div>
                  <span>Shortlisted</span>
                  <strong>{job.shortlisted_count}</strong>
                </div>
                <div>
                  <span>In evaluation</span>
                  <strong>{job.pending_count}</strong>
                </div>
                <div className="stats-caption">
                  <FileText size={19} />
                  <p>
                    Same criteria.
                    <br />A clearer comparison.
                  </p>
                </div>
              </div>
              <div className="section-title">
                <h2>
                  Candidates{" "}
                  <span className="count">
                    {page?.count ?? job.candidate_count}
                  </span>
                </h2>
                <div className="row">
                  {selected.length > 0 && (
                    <button
                      className="secondary"
                      disabled={busy}
                      onClick={() => void bulkShortlist()}
                    >
                      <Check size={15} />
                      Shortlist {selected.length}
                    </button>
                  )}
                  <button
                    className="primary"
                    onClick={() => void evaluate()}
                    disabled={
                      busy ||
                      job.status === "closed" ||
                      job.candidate_count === 0
                    }
                  >
                    <Sparkles size={16} />
                    {busy
                      ? "Working…"
                      : selected.length
                        ? `Evaluate ${selected.length} selected`
                        : "Evaluate candidates"}
                  </button>
                </div>
              </div>
              <div className="table-card">
                <div className="filters">
                  <div className="search">
                    <Search size={17} />
                    <input
                      aria-label="Search candidates"
                      placeholder="Search by name or email"
                      value={search}
                      onChange={(e) => {
                        setSearch(e.target.value);
                        setPageNumber(1);
                      }}
                    />
                  </div>
                  <select
                    aria-label="Filter by stage"
                    value={stage}
                    onChange={(e) => {
                      setStage(e.target.value);
                      setPageNumber(1);
                    }}
                  >
                    <option value="">All stages</option>
                    {Object.entries(stageLabel).map(([v, label]) => (
                      <option key={v} value={v}>
                        {label}
                      </option>
                    ))}
                  </select>
                  <select
                    aria-label="Evaluation status"
                    value={evaluation}
                    onChange={(e) => {
                      setEvaluation(e.target.value);
                      setPageNumber(1);
                    }}
                  >
                    <option value="">All evaluations</option>
                    <option value="completed">Evaluated</option>
                    <option value="queued">Queued</option>
                    <option value="running">Evaluating</option>
                    <option value="failed">Failed</option>
                    <option value="stale">Criteria changed</option>
                  </select>
                  <select
                    aria-label="Minimum score"
                    value={minScore}
                    onChange={(e) => {
                      setMinScore(e.target.value);
                      setPageNumber(1);
                    }}
                  >
                    <option value="">Any score</option>
                    <option value="75">75 and above</option>
                    <option value="50">50 and above</option>
                  </select>
                  <select
                    aria-label="Sort candidates"
                    value={ordering}
                    onChange={(e) => {
                      setOrdering(e.target.value);
                      setPageNumber(1);
                    }}
                  >
                    <option value="score">Highest score</option>
                    <option value="newest">Newest first</option>
                    <option value="name">Name A–Z</option>
                  </select>
                </div>
                {page?.results.length ? (
                  <div className="table-scroll" aria-busy={loading}>
                    <table>
                      <thead>
                        <tr>
                          <th className="checkbox-cell">
                            <input
                              type="checkbox"
                              aria-label="Select page"
                              checked={selected.length === page.results.length}
                              onChange={(e) =>
                                setSelected(
                                  e.target.checked
                                    ? page.results.map((c) => c.id)
                                    : [],
                                )
                              }
                            />
                          </th>
                          <th>Candidate</th>
                          <th>Match score</th>
                          <th>Review signals</th>
                          <th>Stage</th>
                          <th>
                            <span className="sr-only">Open candidate</span>
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {page.results.map((c) => (
                          <tr
                            key={c.id}
                            className={
                              selected.includes(c.id) ? "selected" : ""
                            }
                          >
                            <td>
                              <input
                                type="checkbox"
                                aria-label={`Select ${c.name}`}
                                checked={selected.includes(c.id)}
                                onChange={(e) =>
                                  setSelected((items) =>
                                    e.target.checked
                                      ? [...items, c.id]
                                      : items.filter((id) => id !== c.id),
                                  )
                                }
                              />
                            </td>
                            <td>
                              <button
                                className="candidate-name"
                                onClick={() => reviewCandidate(c.id)}
                              >
                                <span className="avatar">
                                  {c.name
                                    .split(" ")
                                    .slice(0, 2)
                                    .map((n) => n[0])
                                    .join("")}
                                </span>
                                <span>
                                  <strong>{c.name}</strong>
                                  <small>{c.email || c.filename}</small>
                                </span>
                              </button>
                            </td>
                            <td>
                              <Score candidate={c} />
                            </td>
                            <td>
                              {!c.stale &&
                              c.evaluation?.status === "completed" ? (
                                c.evaluation.results.some(
                                  (r) => r.needs_review,
                                ) ? (
                                  <span className="review-flag">
                                    Check evidence
                                  </span>
                                ) : (
                                  <span className="small muted">
                                    Ready for review
                                  </span>
                                )
                              ) : (
                                <span className="muted">—</span>
                              )}
                            </td>
                            <td>
                              <StageBadge stage={c.stage} />
                            </td>
                            <td>
                              <button
                                className="icon-button"
                                aria-label={`Review ${c.name}`}
                                onClick={() => reviewCandidate(c.id)}
                              >
                                <ChevronRight size={18} />
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : loading ? (
                  <div className="empty">Loading candidates…</div>
                ) : (
                  <Empty
                    title={
                      job.candidate_count
                        ? "No candidates match these filters."
                        : "A fresh start for this role."
                    }
                  >
                    {job.candidate_count ? (
                      <p>Try a different search or broaden the filters.</p>
                    ) : (
                      <>
                        <p>Add resumes to begin building your shortlist.</p>
                        <button
                          className="secondary"
                          disabled={job.status === "closed"}
                          onClick={() => setUploading(true)}
                        >
                          <UploadCloud size={16} />
                          Add resumes
                        </button>
                      </>
                    )}
                  </Empty>
                )}
                {page && page.count > 0 && (
                  <div className="pagination">
                    <span>
                      {(pageNumber - 1) * 40 + 1}–
                      {Math.min(pageNumber * 40, page.count)} of {page.count}{" "}
                      candidates
                    </span>
                    <div className="row">
                      <button
                        className="secondary"
                        disabled={!page.previous || loading}
                        onClick={() => setPageNumber((p) => p - 1)}
                      >
                        Previous
                      </button>
                      <button
                        className="secondary"
                        disabled={!page.next || loading}
                        onClick={() => setPageNumber((p) => p + 1)}
                      >
                        Next
                      </button>
                    </div>
                  </div>
                )}
              </div>
              {page?.results.some(
                (candidate) => candidate.evaluation?.status === "completed",
              ) && (
                <div className="table-card matrix-card">
                  <div className="section-title">
                    <h2>Criterion matrix</h2>
                    <span className="small muted">Jev scores by candidate</span>
                  </div>
                  <div className="table-scroll">
                    <table>
                      <thead>
                        <tr>
                          <th>Candidate</th>
                          {job.criteria.map((criterion) => (
                            <th key={criterion.id}>{criterion.name}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {page.results.map((candidate) => (
                          <tr key={candidate.id}>
                            <td>
                              <strong>{candidate.name}</strong>
                            </td>
                            {job.criteria.map((criterion) => {
                              const item = candidate.evaluation?.results.find(
                                (result) => result.id === criterion.id,
                              );
                              return (
                                <td key={criterion.id}>
                                  {item ? `${Math.round(item.score)}/100` : "—"}
                                </td>
                              );
                            })}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
              <div className="page-footnote">
                <span>
                  Scores support your review. Hiring decisions stay with you.
                </span>
                <button
                  className="text-button"
                  disabled={busy}
                  onClick={async () => {
                    setBusy(true);
                    try {
                      await mutation(
                        `jobs/${job.id}/`,
                        { status: job.status === "open" ? "closed" : "open" },
                        "PATCH",
                      );
                      refresh();
                    } catch (e) {
                      setError((e as Error).message);
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  {job.status === "open" ? "Close role" : "Reopen role"}
                </button>
              </div>
            </>
          )}
        </div>
      </main>
      {editor && (
        <JobEditor
          job={editor === "new" ? undefined : editor}
          onClose={() => setEditor(false)}
          onSave={(saved) => {
            setEditor(false);
            void loadJobs()
              .then(() => {
                if (saved.id !== jobId) openJob(saved.id);
                else refresh();
              })
              .catch((e) => setError(e.message));
          }}
        />
      )}{" "}
      {uploading && job && (
        <Upload
          jobId={job.id}
          onClose={() => setUploading(false)}
          onDone={refresh}
        />
      )}{" "}
      {candidateId && job && (
        <CandidatePanel
          key={candidateId}
          id={candidateId}
          job={job}
          onClose={() => setCandidateId(null)}
          onChanged={refresh}
          onNavigate={setCandidateId}
          previous={reviewOrder[candidateIndex - 1]}
          next={reviewOrder[candidateIndex + 1]}
        />
      )}
    </div>
  );
}
function Login({
  session,
  onLogin,
}: {
  session: Session;
  onLogin: (s: Session) => void;
}) {
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const data = Object.fromEntries(new FormData(event.currentTarget));
    setBusy(true);
    setError("");
    try {
      onLogin(await mutation<Session>("login/", data));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <main className="login-page">
      <section className="login-story">
        <span className="brand-mark">
          j<span>j</span>
        </span>
        <p className="eyebrow">HIRELENS</p>
        <h1>
          Less sifting.
          <br />
          More meaningful
          <br />
          conversations.
        </h1>
        <p>
          A thoughtful workspace for finding the people
          <br />
          behind the resumes.
        </p>
        <small>Jobs. Evidence. A shortlist you understand.</small>
      </section>
      <section className="login-form">
        <form onSubmit={submit}>
          <p className="eyebrow">YOUR RECRUITING WORKSPACE</p>
          <h2>Welcome back.</h2>
          <p className="muted">Sign in to pick up where you left off.</p>
          <ErrorMessage message={error} />
          <label>
            Username
            <input name="username" autoComplete="username" required autoFocus />
          </label>
          <label>
            Password
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              required
            />
          </label>
          <button className="primary" disabled={busy}>
            {busy ? "Signing in…" : "Sign in"}
            <ArrowUpRight size={17} />
          </button>
          {session.mode === "demo" && (
            <p className="notice">
              Demo mode is enabled. Sign in with the account created during
              local setup.
            </p>
          )}
          <p className="small muted">
            Accounts are provisioned by your workspace administrator.
          </p>
        </form>
      </section>
    </main>
  );
}
