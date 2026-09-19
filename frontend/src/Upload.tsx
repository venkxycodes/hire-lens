import { useRef, useState, type FormEvent } from "react";
import { UploadCloud, FileText } from "lucide-react";
import { api, mutation } from "./api";
import { ErrorMessage, Modal } from "./components";
type Outcome = { filename: string; status: string; error?: string };
export function Upload({
  jobId,
  onClose,
  onDone,
}: {
  jobId: number;
  onClose: () => void;
  onDone: () => void;
}) {
  const [tab, setTab] = useState("files");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [outcomes, setOutcomes] = useState<Outcome[]>([]);
  const [progress, setProgress] = useState("");
  const input = useRef<HTMLInputElement>(null);
  async function upload(files: File[]) {
    setBusy(true);
    setError("");
    setOutcomes([]);
    try {
      for (let i = 0; i < files.length; i += 20) {
        setProgress(
          `Uploading ${i + 1}–${Math.min(i + 20, files.length)} of ${files.length}`,
        );
        const body = new FormData();
        files.slice(i, i + 20).forEach((file) => body.append("files", file));
        const result = await api<{ results: Outcome[] }>(
          `jobs/${jobId}/resumes/`,
          { method: "POST", body },
        );
        setOutcomes((items) => [...items, ...result.results]);
        onDone();
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
      setProgress("");
      if (input.current) input.current.value = "";
    }
  }
  async function paste(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setError("");
    const data = Object.fromEntries(new FormData(event.currentTarget));
    try {
      const result = await mutation<{ results: Outcome[] }>(
        `jobs/${jobId}/resumes/`,
        data,
      );
      setOutcomes(result.results);
      onDone();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <Modal
      title="Add resumes"
      onClose={() => {
        if (!busy) onClose();
      }}
    >
      <div className="modal-body">
        <p className="muted">
          Add a batch, then evaluate everyone against the same criteria.
        </p>
        <div className="tabs">
          <button
            className={tab === "files" ? "active" : ""}
            onClick={() => setTab("files")}
          >
            Upload files
          </button>
          <button
            className={tab === "text" ? "active" : ""}
            onClick={() => setTab("text")}
          >
            Paste resume
          </button>
        </div>
        <ErrorMessage message={error} />
        {tab === "files" ? (
          <>
            <input
              ref={input}
              type="file"
              multiple
              accept=".pdf,.docx,.txt"
              className="sr-only"
              aria-label="Choose resume files"
              onChange={(e) => void upload(Array.from(e.target.files ?? []))}
              disabled={busy}
            />
            <button
              className="dropzone"
              disabled={busy}
              onClick={() => input.current?.click()}
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => {
                e.preventDefault();
                if (!busy) void upload(Array.from(e.dataTransfer.files));
              }}
            >
              <UploadCloud size={30} />
              <strong>
                {busy ? progress : "Choose files or drop them here"}
              </strong>
              <span>PDF, DOCX, or TXT · 5 MB per file</span>
            </button>
            <p className="small muted">
              Duplicates are skipped. Scanned PDFs need text extraction before
              upload. Files remain private to your workspace.
            </p>
          </>
        ) : (
          <form onSubmit={paste}>
            <label>
              Candidate name
              <input name="name" required maxLength={160} />
            </label>
            <label>
              Email (optional)
              <input name="email" type="email" />
            </label>
            <label>
              Resume text
              <textarea
                name="resume_text"
                rows={9}
                required
                minLength={40}
                maxLength={40000}
              />
            </label>
            <button className="primary" disabled={busy}>
              {busy ? "Adding…" : "Add candidate"}
            </button>
          </form>
        )}
        {outcomes.length > 0 && (
          <div className="upload-results" aria-live="polite">
            {outcomes.map((o, i) => (
              <div key={i}>
                <FileText size={16} />
                <span className="grow">
                  {o.filename}
                  <small>{o.error}</small>
                </span>
                <span className={`badge ${o.status === "failed" ? "red" : ""}`}>
                  {o.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
      <footer>
        <button className="primary" disabled={busy} onClick={onClose}>
          Done
        </button>
      </footer>
    </Modal>
  );
}
