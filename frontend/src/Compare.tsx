import { useEffect, useState, type FormEvent } from "react";
import { FileText, UploadCloud } from "lucide-react";
import { api, mutation } from "./api";
import { ErrorMessage } from "./components";

export function Compare() {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [saved, setSaved] = useState<string[]>([]),
    [selected, setSelected] = useState("");
  const [result, setResult] = useState<any>(null);
  useEffect(() => {
    void api<{ resumes: string[] }>("compare/").then((d) =>
      setSaved(d.resumes),
    );
  }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    try {
      setResult(await mutation("compare/", new FormData(event.currentTarget)));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <section className="compare-card">
      <div className="page-heading">
        <div>
          <p className="eyebrow">ONE-TO-ONE MATCH</p>
          <h1>Compare a resume</h1>
          <p className="muted">
            Choose a saved resume or upload one, then define what matters for
            this JD.
          </p>
        </div>
        <FileText size={28} />
      </div>
      <form onSubmit={submit} className="compare-form">
        <label>
          Job description
          <textarea
            name="job_description"
            minLength={40}
            required
            placeholder="Paste the complete job description…"
          />
        </label>
        <label>
          Comparison criteria
          <span className="small muted">
            One criterion per line: skills, experience, outcomes, or
            requirements.
          </span>
          <textarea
            name="criteria"
            placeholder={
              "Python and Django\nExperience building APIs\nClear ownership and measurable outcomes"
            }
          />
        </label>
        <label>
          Saved resumes
          {saved.length ? (
            <select
              value={selected}
              onChange={(e) => setSelected(e.target.value)}
            >
              <option value="">Choose a saved PDF…</option>
              {saved.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          ) : (
            <span className="muted">No PDFs saved yet.</span>
          )}
          <span className="small muted">Or upload a new PDF</span>
          <input
            name="resume"
            type="file"
            accept="application/pdf"
            required={!selected}
          />
        </label>
        <input type="hidden" name="resume_name" value={selected} />
        <button className="primary" disabled={busy}>
          <UploadCloud size={16} />
          {busy ? "Comparing…" : "Compare resume"}
        </button>
      </form>
      <ErrorMessage message={error} />
      {result && (
        <div className="compare-result">
          <div>
            <span className="eyebrow">{result.verdict}</span>
            <strong>
              {Math.round(result.score)}
              <small>/100</small>
            </strong>
            <p>
              {result.resume_name} · {result.detail}
            </p>
          </div>
          <div>
            <b>Evidence found</b>
            <p className="muted">
              {result.matched_terms.length
                ? result.matched_terms.join(" · ")
                : "No shared signals found"}
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
