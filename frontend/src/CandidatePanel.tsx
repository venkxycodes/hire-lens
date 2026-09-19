import { useEffect, useState } from "react";
import {
  ArrowLeft,
  ArrowRight,
  Download,
  Mail,
  Check,
  RotateCw,
} from "lucide-react";
import { api, mutation } from "./api";
import {
  ErrorMessage,
  Modal,
  Score,
  StageBadge,
  stageLabel,
} from "./components";
import type { CandidateDetail, Job, Stage } from "./types";
export function CandidatePanel({
  id,
  job,
  onClose,
  onChanged,
  previous,
  next,
  onNavigate,
}: {
  id: number;
  job: Job;
  onClose: () => void;
  onChanged: () => void;
  previous?: number;
  next?: number;
  onNavigate: (id: number) => void;
}) {
  const [candidate, setCandidate] = useState<CandidateDetail | null>(null);
  const [name, setName] = useState("");
  const [notes, setNotes] = useState("");
  const [email, setEmail] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [tab, setTab] = useState("evaluation");
  const [subject, setSubject] = useState(
    `Let's talk about the ${job.title} role`,
  );
  const [message, setMessage] = useState("");
  async function load() {
    const c = await api<CandidateDetail>(`applications/${id}/`);
    setCandidate(c);
    return c;
  }
  useEffect(() => {
    let active = true;
    setCandidate(null);
    setError("");
    api<CandidateDetail>(`applications/${id}/`)
      .then((c) => {
        if (active) {
          setCandidate(c);
          setName(c.name);
          setNotes(c.notes);
          setEmail(c.email);
          setSubject(
            c.outreach_subject || `Let's talk about the ${job.title} role`,
          );
          setMessage(
            c.outreach_body ||
              `Hi ${c.name.split(" ")[0]},\n\nYour experience caught my attention for our ${job.title} role. I'd love to learn more about your work and share what the team is building.\n\nWould you be open to a short conversation this week?\n\nBest,`,
          );
        }
      })
      .catch((e) => {
        if (active) setError(e.message);
      });
    return () => {
      active = false;
    };
  }, [id, job.title]);
  async function save(changes: object) {
    setBusy(true);
    setError("");
    try {
      const c = await mutation<CandidateDetail>(
        `applications/${id}/`,
        changes,
        "PATCH",
      );
      setCandidate(c);
      onChanged();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  async function retry() {
    setBusy(true);
    setError("");
    try {
      await mutation(`jobs/${job.id}/evaluate/`, { application_ids: [id] });
      await load();
      onChanged();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const e = candidate?.evaluation;
  const defaultMessage = candidate
    ? `Hi ${candidate.name.split(" ")[0]},\n\nYour experience caught my attention for our ${job.title} role. I'd love to learn more about your work and share what the team is building.\n\nWould you be open to a short conversation this week?\n\nBest,`
    : "";
  const draftDirty =
    !!candidate &&
    (subject !==
      (candidate.outreach_subject ||
        `Let's talk about the ${job.title} role`) ||
      message !== (candidate.outreach_body || defaultMessage));
  const dirty =
    !!candidate &&
    (notes !== candidate.notes ||
      name !== candidate.name ||
      email !== candidate.email ||
      draftDirty);
  function leave(action: () => void) {
    if (
      !busy &&
      (!dirty ||
        window.confirm("You have unsaved changes. Leave without saving?"))
    )
      action();
  }
  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (dirty) event.preventDefault();
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);
  return (
    <Modal title="Candidate review" onClose={() => leave(onClose)} wide>
      <div className="modal-body">
        <ErrorMessage message={error} />
        {!candidate ? (
          <p>Loading candidate…</p>
        ) : (
          <>
            <div className="candidate-heading">
              <div className="avatar large">
                {candidate.name
                  .split(" ")
                  .slice(0, 2)
                  .map((n) => n[0])
                  .join("")}
              </div>
              <div className="grow">
                <h2>{candidate.name}</h2>
                <p className="muted">{candidate.email || candidate.filename}</p>
                <StageBadge stage={candidate.stage} />
              </div>
              <Score candidate={candidate} />
            </div>
            <div className="row wrap review-actions">
              <button
                className="primary"
                disabled={busy || candidate.stage === "shortlisted"}
                onClick={() => void save({ stage: "shortlisted" })}
              >
                <Check size={16} />
                Shortlist
              </button>
              <label className="inline-label">
                Stage
                <select
                  aria-label="Candidate stage"
                  value={candidate.stage}
                  onChange={(event) => void save({ stage: event.target.value })}
                  disabled={busy}
                >
                  {Object.entries(stageLabel).map(([value, label]) => (
                    <option value={value} key={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </label>
              <button className="secondary" onClick={() => setTab("outreach")}>
                <Mail size={16} />
                Draft outreach
              </button>
            </div>
            <div className="tabs">
              {[
                ["evaluation", "Evaluation"],
                ["resume", "Resume"],
                ["notes", "Notes & activity"],
                ["outreach", "Outreach"],
              ].map(([value, label]) => (
                <button
                  className={tab === value ? "active" : ""}
                  key={value}
                  onClick={() => setTab(value)}
                >
                  {label}
                </button>
              ))}
            </div>
            {tab === "evaluation" && (
              <>
                {candidate.stale && (
                  <p className="notice">
                    This evaluation uses an older rubric or scoring
                    configuration. Re-evaluate before comparing scores.
                  </p>
                )}
                {e?.provider === "demo" && (
                  <p className="notice">
                    Demo evaluation: illustrative keyword matching, not a Jev
                    result. Do not use these scores for hiring decisions.
                  </p>
                )}
                {e?.status === "failed" && <ErrorMessage message={e.error} />}
                {(!e || candidate.stale || e.status === "failed") && (
                  <button
                    className="secondary"
                    disabled={busy || job.status === "closed"}
                    onClick={() => void retry()}
                  >
                    <RotateCw size={15} />
                    Evaluate candidate
                  </button>
                )}
                {e && ["queued", "running"].includes(e.status) && (
                  <div className="notice">
                    Evaluation is {e.status}.{" "}
                    <button
                      className="text-button"
                      onClick={() =>
                        void load().catch((e) => setError(e.message))
                      }
                    >
                      Refresh result
                    </button>
                  </div>
                )}
                {e?.status === "completed" && (
                  <>
                    <div className="section-title">
                      <h3>Match by criterion</h3>
                      <span className="small muted">
                        Criteria v{e.job_version} ·{" "}
                        {Math.round((e.confidence ?? 0) * 100)}% model
                        confidence
                      </span>
                    </div>
                    {e.results.map((c) => (
                      <div className="criterion-result" key={c.id}>
                        <div className="row between">
                          <strong>
                            {c.name}{" "}
                            {c.required && (
                              <span className="required">Required</span>
                            )}
                          </strong>
                          <strong>
                            {Math.round(c.score)}
                            <span className="muted"> / 100</span>
                          </strong>
                        </div>
                        <p className="small muted">{c.description}</p>
                        <div className="meter">
                          <span style={{ width: `${c.score}%` }} />
                        </div>
                        <div className="row between small">
                          <span className="muted">
                            Weight {c.weight} · Confidence{" "}
                            {Math.round(c.confidence * 100)}%
                          </span>
                          {c.needs_review && (
                            <span className="review-flag">Review evidence</span>
                          )}
                        </div>
                      </div>
                    ))}
                    <p className="small muted">
                      Scores reflect documented evidence, not a candidate's
                      potential. Missing evidence is not proof of a missing
                      skill. Model confidence is not the probability of job
                      success.
                    </p>
                  </>
                )}
                {candidate.history.length > 1 && (
                  <details>
                    <summary>
                      Evaluation history ({candidate.history.length})
                    </summary>
                    {candidate.history.map((h) => (
                      <p className="small" key={h.id}>
                        Criteria v{h.job_version} · {h.status} ·{" "}
                        {h.score ?? "—"}/100 · {h.provider}
                      </p>
                    ))}
                  </details>
                )}
              </>
            )}
            {tab === "resume" && (
              <>
                <div className="section-title">
                  <h3>Resume text</h3>
                  {candidate.filename !== "Pasted resume" && (
                    <a
                      className="secondary"
                      href={`/api/v1/applications/${id}/resume/`}
                    >
                      <Download size={15} />
                      Original file
                    </a>
                  )}
                </div>
                <pre className="resume-text">{candidate.resume_text}</pre>
              </>
            )}
            {tab === "notes" && (
              <>
                <div className="form-grid">
                  <label>
                    Candidate name
                    <input
                      value={name}
                      maxLength={160}
                      onChange={(event) => setName(event.target.value)}
                    />
                  </label>
                  <label>
                    Candidate email
                    <input
                      type="email"
                      value={email}
                      onChange={(event) => setEmail(event.target.value)}
                    />
                  </label>
                </div>
                <button
                  className="secondary"
                  disabled={
                    busy ||
                    !name.trim() ||
                    (name === candidate.name && email === candidate.email)
                  }
                  onClick={() => void save({ name, email })}
                >
                  Save contact details
                </button>
                <label>
                  Recruiter notes
                  <textarea
                    rows={7}
                    value={notes}
                    maxLength={20000}
                    onChange={(event) => setNotes(event.target.value)}
                    placeholder="What stood out? What should you ask in a conversation?"
                  />
                </label>
                <button
                  className="primary"
                  disabled={busy || notes === candidate.notes}
                  onClick={() => void save({ notes })}
                >
                  Save notes
                </button>
                <h3 className="space-top">Activity</h3>
                {candidate.activity.length ? (
                  candidate.activity.map((a, i) => (
                    <div className="activity" key={i}>
                      <span>{a.message}</span>
                      <time>{new Date(a.created_at).toLocaleString()}</time>
                    </div>
                  ))
                ) : (
                  <p className="muted">No review activity yet.</p>
                )}
              </>
            )}
            {tab === "outreach" && (
              <>
                <p className="muted">
                  Make the introduction your own. Opening a draft does not send
                  it or change the candidate's stage.
                </p>
                <label>
                  Candidate email
                  <input
                    type="email"
                    value={email}
                    onChange={(event) => setEmail(event.target.value)}
                  />
                </label>
                {email !== candidate.email && (
                  <button
                    className="secondary"
                    disabled={busy}
                    onClick={() => void save({ email })}
                  >
                    Save email
                  </button>
                )}
                <label>
                  Subject
                  <input
                    value={subject}
                    onChange={(event) => setSubject(event.target.value)}
                  />
                </label>
                <label>
                  Message
                  <textarea
                    rows={9}
                    value={message}
                    onChange={(event) => setMessage(event.target.value)}
                  />
                </label>
                <div className="row wrap">
                  <button
                    className="secondary"
                    disabled={busy || !draftDirty}
                    onClick={() =>
                      void save({
                        outreach_subject: subject,
                        outreach_body: message,
                      })
                    }
                  >
                    Save draft
                  </button>
                  <a
                    className={`primary ${!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) ? "disabled" : ""}`}
                    href={`mailto:${encodeURIComponent(email)}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(message)}`}
                  >
                    <Mail size={16} />
                    Open email draft
                  </a>
                  <button
                    className="secondary"
                    disabled={busy || candidate.stage === "contacted"}
                    onClick={() => void save({ stage: "contacted" as Stage })}
                  >
                    Mark as contacted
                  </button>
                </div>
              </>
            )}
          </>
        )}
      </div>
      <footer className="between">
        <span className="small muted">Your judgment makes the final call.</span>
        <div className="row">
          <button
            className="secondary"
            disabled={!previous || busy}
            onClick={() => previous && leave(() => onNavigate(previous))}
          >
            <ArrowLeft size={16} />
            Previous
          </button>
          <button
            className="secondary"
            disabled={!next || busy}
            onClick={() => next && leave(() => onNavigate(next))}
          >
            Next
            <ArrowRight size={16} />
          </button>
        </div>
      </footer>
    </Modal>
  );
}
