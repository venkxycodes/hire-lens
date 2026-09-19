import { useState, type FormEvent } from "react";
import { Plus, Trash2 } from "lucide-react";
import { mutation } from "./api";
import { ErrorMessage, Modal } from "./components";
import type { Criterion, Job } from "./types";
const defaults: Criterion[] = [
  {
    id: "core-skills",
    name: "Core skills",
    description:
      "Applied experience with the primary skills and technologies required in the job description.",
    weight: 50,
    required: true,
  },
  {
    id: "relevant-experience",
    name: "Relevant experience",
    description:
      "Direct experience delivering the responsibilities described for this role.",
    weight: 30,
    required: true,
  },
  {
    id: "ownership",
    name: "Ownership & outcomes",
    description:
      "Evidence of independently owning work and delivering concrete outcomes relevant to this role.",
    weight: 20,
    required: false,
  },
];
export function JobEditor({
  job,
  onClose,
  onSave,
}: {
  job?: Job;
  onClose: () => void;
  onSave: (job: Job) => void;
}) {
  const [title, setTitle] = useState(job?.title ?? "");
  const [department, setDepartment] = useState(job?.department ?? "");
  const [location, setLocation] = useState(job?.location ?? "");
  const [description, setDescription] = useState(job?.description ?? "");
  const [criteria, setCriteria] = useState<Criterion[]>(
    job?.criteria ?? defaults,
  );
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const total = criteria.reduce((sum, c) => sum + c.weight, 0);
  function update(index: number, changes: Partial<Criterion>) {
    setCriteria((items) =>
      items.map((c, i) => (i === index ? { ...c, ...changes } : c)),
    );
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      onSave(
        await mutation<Job>(
          job ? `jobs/${job.id}/` : "jobs/",
          { title, department, location, description, criteria },
          job ? "PATCH" : "POST",
        ),
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setSaving(false);
    }
  }
  return (
    <Modal
      title={job ? "Edit role & criteria" : "Create a role"}
      onClose={onClose}
      wide
    >
      <form onSubmit={submit}>
        <div className="modal-body">
          <p className="muted">
            Describe the work. Define what a strong candidate should
            demonstrate.
          </p>
          <ErrorMessage message={error} />
          <label>
            Job title
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
              maxLength={160}
              placeholder="e.g. Senior Backend Engineer"
              autoFocus
            />
          </label>
          <div className="form-grid">
            <label>
              Department
              <input
                value={department}
                onChange={(e) => setDepartment(e.target.value)}
                maxLength={120}
                placeholder="Engineering"
              />
            </label>
            <label>
              Location
              <input
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                maxLength={120}
                placeholder="Remote · US"
              />
            </label>
          </div>
          <label>
            Job description
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              required
              rows={7}
              maxLength={20000}
              placeholder="Responsibilities, skills, and what success looks like…"
            />
          </label>
          <div className="section-title">
            <h3>Evaluation criteria</h3>
            <span className="muted">Weights normalized to 100%</span>
          </div>
          <p className="small muted">
            Use specific, job-related skills. Required criteria flag gaps for
            your review; they never automatically reject a candidate.
          </p>
          {criteria.map((c, i) => (
            <fieldset className="criterion-editor" key={c.id}>
              <legend>Criterion {i + 1}</legend>
              <div className="criterion-head">
                <label className="grow">
                  Name
                  <input
                    value={c.name}
                    onChange={(e) => update(i, { name: e.target.value })}
                    required
                    maxLength={100}
                  />
                </label>
                <label className="weight-input">
                  Weight
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={c.weight}
                    onChange={(e) =>
                      update(i, { weight: Number(e.target.value) })
                    }
                    required
                  />
                </label>
                <button
                  type="button"
                  className="icon-button"
                  disabled={criteria.length === 1}
                  onClick={() =>
                    setCriteria((items) => items.filter((_, j) => j !== i))
                  }
                  aria-label={`Remove ${c.name}`}
                >
                  <Trash2 size={17} />
                </button>
              </div>
              <label>
                What should the resume demonstrate?
                <textarea
                  rows={2}
                  value={c.description}
                  onChange={(e) => update(i, { description: e.target.value })}
                  required
                  maxLength={1000}
                />
              </label>
              <div className="row between">
                <label className="check">
                  <input
                    type="checkbox"
                    checked={c.required}
                    onChange={(e) => update(i, { required: e.target.checked })}
                  />
                  Required for the role
                </label>
                <span className="small muted">
                  {total ? Math.round((c.weight / total) * 100) : 0}% of total
                  score
                </span>
              </div>
            </fieldset>
          ))}
          <button
            type="button"
            className="secondary"
            disabled={criteria.length >= 12}
            onClick={() =>
              setCriteria((items) => [
                ...items,
                {
                  id: crypto.randomUUID(),
                  name: "",
                  description: "",
                  weight: 10,
                  required: false,
                },
              ])
            }
          >
            <Plus size={16} />
            Add criterion
          </button>
          {job && (
            <p className="notice">
              Changing the title, description, or criteria marks existing scores
              as outdated. Re-evaluate candidates to compare them on the new
              criteria.
            </p>
          )}
        </div>
        <footer>
          <button type="button" className="secondary" onClick={onClose}>
            Cancel
          </button>
          <button className="primary" disabled={saving}>
            {saving ? "Saving…" : job ? "Save changes" : "Create role"}
          </button>
        </footer>
      </form>
    </Modal>
  );
}
