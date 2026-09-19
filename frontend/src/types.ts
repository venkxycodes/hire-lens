export type Criterion = {
  id: string;
  name: string;
  description: string;
  weight: number;
  required: boolean;
};
export type Job = {
  id: number;
  title: string;
  department: string;
  location: string;
  description: string;
  criteria: Criterion[];
  version: number;
  status: "open" | "closed";
  candidate_count: number;
  shortlisted_count: number;
  pending_count: number;
};
export type Evaluation = {
  id: number;
  job_version: number;
  status: "queued" | "running" | "completed" | "failed";
  provider: string;
  model: string;
  score: number | null;
  confidence: number | null;
  results: (Criterion & {
    score: number;
    confidence: number;
    needs_review: boolean;
    probabilities: Record<string, number>;
  })[];
  error: string;
  attempts: number;
  completed_at: string | null;
};
export type Stage = "new" | "shortlisted" | "hold" | "rejected" | "contacted";
export type Candidate = {
  id: number;
  job: number;
  name: string;
  email: string;
  filename: string;
  stage: Stage;
  notes: string;
  outreach_subject: string;
  outreach_body: string;
  evaluation: Evaluation | null;
  stale: boolean;
  created_at: string;
};
export type CandidateDetail = Candidate & {
  resume_text: string;
  history: Evaluation[];
  activity: { message: string; created_at: string }[];
};
export type Session = {
  user: string | null;
  csrf_token: string;
  mode: string;
  jev_configured: boolean;
};
export type Page<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
