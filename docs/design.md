# Product and interface design

## Recruiter flow

1. **Roles:** scan open roles and candidate/shortlist counts.
2. **Role setup:** paste the JD; write atomic, job-related criteria and relative weights. Required criteria produce review signals, never automatic rejection.
3. **Intake:** upload multiple files, in requests of at most 20. Each file reports added, duplicate, or failed; failures do not roll back other candidates. Candidate name/email extraction is a convenience and can be corrected.
4. **Evaluate:** submit all candidates or the selected subset. The request queues durable database records and returns immediately. Current successful results are reused; failed work can be retried.
5. **Review:** rank on current completed scores; filter/search; inspect criterion results and source resume. Old results, pending work, and errors are distinct states. The open review session keeps a stable previous/next sequence while the table refreshes.
6. **Follow up:** shortlist or hold manually, write notes, save a personalized email draft, open it in an email app, then manually mark contacted.

The visual language is deliberately restrained: warm white surfaces, muted green, sparse icons, compact tables, and conventional controls. Responsive layouts preserve the same workflow. Modal dialogs have native focus management and Escape handling; unsaved candidate edits warn before navigation.

## Interface alternatives considered

**Minimal evaluation module:** `start(job_id, application_ids)` and `get(run_id)`. Hides queueing, snapshots, and provider calls behind two operations. Easy for callers, but a run entity adds another lifecycle when the primary screen needs per-candidate progress.

**Fully versioned resources:** separate job versions, upload batches, evaluation runs, retries, and result resources. Gives clients explicit audit control but exposes more concepts and coordination than the first recruiter workflow needs.

**Job-centered workflow (selected):** jobs own criteria and applications; each application points to its latest immutable-input evaluation. `POST jobs/{id}/evaluate/` and paginated application reads hide queue details. Job versions plus provider/model/prompt identities preserve historical meaning. This combines the minimal scoring seam with the flexible design's snapshots and audit requirements without adding run/batch screens.

## API

Base path: `/api/v1/`. JSON except file upload/download. Session cookie authentication; unsafe requests require `X-CSRFToken`. `GET session/` returns the token and sign-in state. Access is scoped by `Job.owner`; another user's IDs return 404.

| Method | Path | Behavior |
|---|---|---|
| GET | `session/` | Username, CSRF token, provider mode and configuration status |
| POST | `login/` | `{username, password}`; rotates session and CSRF token |
| DELETE | `session/` | Sign out |
| GET / POST | `jobs/` | List/create jobs |
| GET / PATCH | `jobs/{id}/` | Read/update role; scoring input changes increment version |
| POST | `jobs/{id}/resumes/` | Multipart repeated `files`, or `{name, email?, resume_text}` |
| POST | `jobs/{id}/evaluate/` | Optional `{application_ids: number[]}`; omitted selects all; returns `{queued}` with 202 |
| GET | `applications/` | Paginated candidate search and ranking |
| GET / PATCH | `applications/{id}/` | Detail/history or update name, email, stage, notes, outreach_subject, outreach_body |
| GET | `applications/{id}/resume/` | Authorized original file download; pasted resumes have text only |
| GET | `health` | Public liveness check inherited from base |

`applications/` filters: `job`, `search` (name/email), `stage`, `evaluation` (`completed`, `queued`, `running`, `failed`, `stale`), `min_score` (0–100), `ordering` (`score`, `name`, `newest`), and `page`. Pages have 40 items and `{count,next,previous,results}`. Stable ID tie-breaking avoids ambiguous equal-score ordering. Stale/incomplete results have no current ranking score.

Job example:

```json
{
  "title": "Backend Engineer",
  "department": "Engineering",
  "location": "Remote",
  "description": "Build reliable Django APIs with PostgreSQL.",
  "criteria": [
    {"id": "django", "name": "Django APIs", "description": "Direct experience delivering Django REST APIs in production", "weight": 70, "required": true},
    {"id": "data", "name": "Data modeling", "description": "PostgreSQL schema and query design", "weight": 30, "required": false}
  ]
}
```

Stages: `new`, `shortlisted`, `hold`, `rejected`, `contacted`. Stage/note changes produce activity events. Saving a draft does not contact a candidate.

## Scoring contract

`recruiting/scoring.py` owns the versioned instructions, five explicit rubric levels, HTTP request shape, strict answer validation, and pure aggregation. The evaluator is injected into `process_one` in tests; demo and live adapters share the same response contract.

Jev Score positions range from 0 through 4 for this rubric. Each dimension is normalized to 0–100, then combined as:

`sum(normalized_score × weight) / sum(weight)`

Validate exact criterion IDs, answer types, finite bounded numbers, probability keys/sums, and agreement between expected score and the probability distribution. A malformed answer fails the evaluation; failures never become zero scores. Required criteria below 75 or confidence below 0.65 receive review signals. These are review heuristics, not validated hiring thresholds.

Jev does not generate explanations or evidence quotes. The app does not invent them: it shows the rubric, criterion results, model confidence, and original resume text for human inspection. A low score means weak documented evidence, not proof of inability.

## Persistence and queue

- **Job:** owner, JD, criteria, version, open/closed status.
- **Application:** immutable resume text/hash/file, contact details, recruiter stage/notes/drafts, latest evaluation reference.
- **Evaluation:** frozen JD/criteria/prompt snapshot, provider/model/prompt identity, status, results, aggregate score, attempts, lease and completion timestamps.
- **Activity:** manual stage/note updates with actor and time.

The evaluation identity `(application, job_version, provider, model, prompt_version)` makes repeated submission idempotent and supports changing from demo to live without mixing results. Job row locking serializes scoring submission and rubric edits. Candidate updates bind to their locked instance so notes cannot overwrite a concurrent evaluation pointer.

Workers claim records using a conditional database update and unique lease token. Network calls happen outside a transaction; only the current lease owner may publish. Leases expire after two minutes, each request times out after 45 seconds, transient provider failures get bounded exponential retries, and three interrupted/failed attempts become visible failures. Database connection failures trigger connection cleanup and a short backoff. PostgreSQL supports concurrent workers; SQLite is intended for one local worker.

## Scaling boundaries

Ranking/search/pagination happen server-side. Each resume is one provider request containing all criteria. Thousands of resumes are accepted in successive upload batches; no single browser request sends the entire corpus to Jev. Queue throughput is limited by configured worker processes and provider limits. This is not a claim of load-tested thousand-resume throughput. The API currently lists all jobs for its owner, and a candidate detail returns its evaluation history; add pagination there if actual usage justifies it.
