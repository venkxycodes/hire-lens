import { useState, type FormEvent } from "react";
import { FileText, UploadCloud } from "lucide-react";
import { api, mutation } from "./api";
import { ErrorMessage } from "./components";

export function Compare() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState<string[]>([]);
  const [selected, setSelected] = useState("");
  const [result, setResult] = useState<{
    score: number;
    filename: string;
    resume_name: string;
    matched_terms: string[];
  } | null>(null);
  useState(() => {
    void api<{ resumes: string[] }>("compare/").then((data) =>
      setSaved(data.resumes),
    );
  });
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    setResult(null);
    const data = new FormData(event.currentTarget);
    try {
      setResult(await mutation("compare/", data));
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
            Paste a JD and upload one PDF. The file is saved to your local
            resume corpus.
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
          Resume PDF
          <input name="resume" type="file" accept="application/pdf" required />
        </label>
        <button className="primary" disabled={busy}>
          <UploadCloud size={16} />
          {busy ? "Comparing…" : "Compare resume"}
        </button>
      </form>
      <ErrorMessage message={error} />
      {result && (
        <div className="compare-result">
          <div>
            <span className="eyebrow">MATCH SCORE</span>
            <strong>
              {Math.round(result.score)}
              <small>/100</small>
            </strong>
            <p>
              {result.resume_name} · saved as {result.filename}
            </p>
          </div>
          <div>
            <b>Matching terms</b>
            <p className="muted">
              {result.matched_terms.length
                ? result.matched_terms.join(" · ")
                : "No shared terms found"}
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
