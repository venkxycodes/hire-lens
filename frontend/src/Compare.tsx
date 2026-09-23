import { useEffect, useState, type FormEvent } from "react";
import { FileText, UploadCloud } from "lucide-react";
import { api } from "./api";
import { ErrorMessage } from "./components";

export function Compare() {
  const [busy, setBusy] = useState(false),
    [error, setError] = useState("");
  const [saved, setSaved] = useState<string[]>([]),
    [selected, setSelected] = useState("");
  const [result, setResult] = useState<any>(null);
  const [jobDescription, setJobDescription] = useState("");
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
      const form = new FormData(event.currentTarget);
      const draft = await api<{
        criteria: { name: string; description: string }[];
        provider?: string;
        model?: string;
        failure_reason?: string;
      }>("rubric-draft/", {
        method: "POST",
        body: JSON.stringify({ description: form.get("job_description") }),
      });
      form.set(
        "criteria",
        draft.criteria
          .map((item) => `${item.name}: ${item.description}`)
          .join("\n"),
      );
      form.set("rubric_provider", draft.provider || "unknown");
      form.set("rubric_model", draft.model || "");
      form.set("rubric_failure_reason", draft.failure_reason || "");
      setResult(await api("compare/", { method: "POST", body: form }));
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
            Paste a JD and choose a resume. HireLens will define the rubric,
            score the resume with Jev, and show the evidence by criterion.
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
            value={jobDescription}
            onChange={(e) => setJobDescription(e.target.value)}
            placeholder="Paste the complete job description…"
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
            <b>Criteria scores</b>
            {result.criteria_results?.map((item: any) => (
              <p className="small" key={item.id}>
                {item.name}: <strong>{Math.round(item.score)}/100</strong>
              </p>
            ))}
          </div>
        </div>
      )}
    </section>
  );
}
