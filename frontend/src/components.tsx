import { useEffect, useRef, type ReactNode } from "react";
import { X } from "lucide-react";
import type { Candidate, Stage } from "./types";
export const stageLabel: Record<Stage, string> = {
  new: "To review",
  shortlisted: "Shortlisted",
  hold: "On hold",
  rejected: "Not proceeding",
  contacted: "Contacted",
};
export function StageBadge({ stage }: { stage: Stage }) {
  return <span className={`badge stage-${stage}`}>{stageLabel[stage]}</span>;
}
export function Score({ candidate }: { candidate: Candidate }) {
  const e = candidate.evaluation;
  if (candidate.stale)
    return <span className="badge amber">Criteria changed</span>;
  if (!e) return <span className="muted">Not evaluated</span>;
  if (e.status === "failed")
    return <span className="badge red">Evaluation failed</span>;
  if (e.status !== "completed")
    return (
      <span className="badge">
        {e.status === "queued" ? "Queued" : "Evaluating…"}
      </span>
    );
  return (
    <span className={`score ${(e.score ?? 0) >= 75 ? "good" : ""}`}>
      {Math.round(e.score ?? 0)}
      <span>/100</span>
      {e.provider === "demo" && <small>DEMO</small>}
    </span>
  );
}
export function Modal({
  title,
  children,
  onClose,
  wide = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  wide?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const dialog = ref.current;
    dialog?.showModal();
    return () => dialog?.close();
  }, []);
  return (
    <dialog
      className={wide ? "modal wide" : "modal"}
      ref={ref}
      onCancel={(e) => {
        e.preventDefault();
        onClose();
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <header>
        <h2>{title}</h2>
        <button
          className="icon-button"
          onClick={onClose}
          aria-label="Close dialog"
        >
          <X size={20} />
        </button>
      </header>
      {children}
    </dialog>
  );
}
export function ErrorMessage({ message }: { message: string }) {
  return message ? (
    <div className="error" role="alert">
      {message}
    </div>
  ) : null;
}
export function Empty({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="empty">
      <div className="empty-mark">↗</div>
      <h2>{title}</h2>
      <div className="muted">{children}</div>
    </div>
  );
}
