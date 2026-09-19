# HireLens Improvement Specification

## 1. Purpose

HireLens should evolve from a resume scoring workspace into a **semantic hiring decision engine**.

The product should not attempt to replace the full operational surface of an ATS such as Greenhouse, Lever, or Workday. Those systems can remain systems of record for applications and recruiting workflows. HireLens should specialize in the decision layer: turning an ambiguous role into an explicit hiring rubric, evaluating every candidate against that rubric, and giving recruiters inspectable semantic data rather than an opaque AI recommendation.

The core product principle is:

> A low score means weak documented evidence for a criterion, not proof that a candidate lacks the underlying ability.

HireLens provides decision support. It does not autonomously decide who should be hired or rejected.

## 2. Current State

HireLens currently supports:

- Recruiter-defined roles with a job description.
- Up to 12 atomic weighted criteria.
- Required-criterion flags.
- Resume ingestion from PDF, DOCX, text files, or pasted text.
- Criterion-level Jev scoring and confidence.
- Weighted aggregate candidate scores.
- Review signals for weak required criteria and low-confidence results.
- Durable asynchronous evaluation with retries and recovery.
- Versioned jobs, criteria, prompts, providers, and models.
- Historical evaluation preservation and stale-result detection.
- Candidate ranking, filtering, shortlisting, notes, and outreach drafts.

The current evaluation model is approximately:

```text
Job description
      +
Recruiter-defined criteria
      +
Resume
      |
      v
     Jev
      |
      +-- criterion 1: score + confidence
      +-- criterion 2: score + confidence
      +-- ...
      +-- criterion N: score + confidence
      |
      v
Weighted aggregate score
      |
      v
Recruiter review
```

This is a strong evaluation foundation. The main limitation is that HireLens assumes the recruiter has already translated the role into a good rubric and ultimately collapses a multidimensional candidate into a single aggregate score.

## 3. Target Product Model

HireLens should treat a candidate as a vector of semantic judgments rather than primarily as a scalar score.

For example:

```text
Candidate
[
  backend_systems:      0.96,
  distributed_systems:  0.91,
  golang:               0.88,
  aws:                  0.82,
  kubernetes:           0.74,
  event_driven_systems: 0.93
]
```

The aggregate score remains useful for sorting, but the criterion vector becomes the primary data model exposed to recruiters.

The target pipeline is:

```text
                     LLM
                      |
Job description ---> Role decomposition
                      |
                Draft hiring rubric
                      |
                 Human approval
                      |
                      v
Resume ------------> Jev
                      |
              Semantic decisions
                      |
                      v
               Criterion vector
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       Ranking     Filtering    Evidence
          |           |           |
          +-----------+-----------+
                      |
                      v
               Recruiter decision
```

## 4. Improvement 1: JD-to-Rubric Generation

### Problem

The recruiter currently has to manually translate a job description into atomic criteria. This assumes the recruiter knows how to construct a high-quality evaluation rubric and creates unnecessary setup work.

Job descriptions also mix fundamentally different concepts:

- hard eligibility constraints,
- core functional capabilities,
- technologies,
- domain experience,
- preferences,
- vague behavioral expectations,
- boilerplate.

These should not automatically have equivalent meaning or weight.

### Proposed behavior

When a recruiter creates a role, HireLens should generate a draft rubric from the job description.

A criterion should contain at least:

```json
{
  "id": "distributed-systems",
  "name": "Distributed systems",
  "description": "Evidence of designing, building, or operating distributed production systems",
  "category": "core_capability",
  "required": true,
  "suggested_weight": 9
}
```

Supported categories should initially include:

- `eligibility`
- `core_capability`
- `technology`
- `domain_experience`
- `preferred`
- `behavioral`

### Human approval

Generated criteria must never immediately become the scoring rubric.

The recruiter must be able to:

- add criteria,
- remove criteria,
- edit wording,
- change required status,
- change weights,
- merge redundant criteria,
- approve the final rubric.

Only the approved rubric is used by Jev.

### Architecture

Use an LLM for role decomposition because this step requires open-ended interpretation and structured generation.

Jev remains responsible for repeated semantic evaluation once the dimensions have been defined.

```text
LLM = understand and structure the hiring problem
Jev = execute repeated semantic judgments
Human = define priorities and make hiring decisions
```

### Versioning

Approval or modification of generated criteria must use the existing job-versioning semantics. Changing the effective rubric makes previous evaluations stale.

## 5. Improvement 2: Criterion Matrix as the Primary Review Surface

### Problem

An aggregate score destroys useful information.

Two candidates can receive the same aggregate score while having completely different capability profiles.

### Proposed behavior

Add a matrix-oriented candidate review surface.

Example:

```text
              Go   DistSys   AWS   K8s   Events
Candidate A   92      96      85    78     91
Candidate B   88      72      95    91     40
Candidate C   65      94      80    85     88
```

The recruiter should be able to understand the shape of a candidate before opening the full resume.

### Requirements

- Display normalized criterion scores.
- Surface confidence separately from score.
- Clearly identify required criteria.
- Clearly identify low-confidence judgments.
- Distinguish missing/failed/stale evaluations from low scores.
- Preserve aggregate score as an optional sorting mechanism.
- Allow matrix columns to be sorted by individual criterion.
- Allow recruiters to select which criteria appear as columns.
- Do not visually imply that small score differences are necessarily meaningful.

### API implications

The application list API should expose sufficient current criterion-level data for the matrix without requiring one detail request per candidate.

Pagination must remain server-side.

## 6. Improvement 3: Semantic Candidate Filtering

### Problem

Traditional ATS search is largely based on structured fields, keywords, boolean search, and increasingly semantic retrieval.

HireLens already produces something more useful: structured semantic judgments against role-specific criteria. Those judgments should become queryable.

### Proposed behavior

Recruiters should be able to filter candidates using criterion scores.

Conceptually:

```text
distributed_systems >= 80
AND
(go >= 70 OR python >= 70)
AND
aws >= 60
```

The initial UI does not need to expose a textual query language. A visual filter builder is sufficient.

Example:

```text
Distributed systems   >= Strong
AND
Go                    >= Moderate
AND
Kubernetes            >= Moderate
```

### Requirements

- Filter on one or more criteria.
- Support AND composition initially.
- Add OR groups where useful.
- Filter by score/rubric level.
- Optionally filter by minimum confidence.
- Combine semantic filters with existing stage/search/status filters.
- Execute filtering server-side.
- Do not trigger new Jev evaluations when filters change.

This is an important architectural property: semantic interpretation happens during evaluation, while recruiter exploration operates over persisted structured judgments.

## 7. Improvement 4: Evidence Retrieval

### Problem

Jev currently returns score and confidence but does not provide evidence quotations.

HireLens should not fabricate explanations for Jev's output. However, recruiters need to quickly inspect what in the resume may support a criterion.

### Proposed behavior

For each criterion, independently retrieve the most relevant resume passages.

Example:

```text
Criterion: Distributed systems

Jev score: 4 / 4
Confidence: 0.93

Relevant resume evidence:

"Built high-throughput event ingestion services in Go..."

"Redesigned Kinesis consumers to process only relevant events..."
```

The UI must describe these as **relevant evidence** rather than as Jev's reasoning.

### Retrieval architecture

```text
Resume
  |
  +--> chunking / section detection
             |
             v
       evidence retrieval
             |
             v
       relevant passages

Resume + criterion
        |
        v
       Jev
        |
        v
score + confidence
```

These paths remain logically independent.

### Initial retrieval options

Candidate implementations include:

- lexical/BM25 retrieval,
- embeddings,
- hybrid lexical + semantic retrieval.

The retrieval system should be evaluated before choosing unnecessary complexity.

### Requirements

- Store source offsets or equivalent provenance.
- Preserve the exact source resume text.
- Never generate quotations.
- Allow the recruiter to jump from evidence to the corresponding resume context.
- Return no evidence when retrieval confidence/relevance is insufficient rather than forcing a result.

## 8. Improvement 5: Evaluation and Calibration Framework

### Problem

A technically sophisticated matching system is not useful unless its judgments are reliable.

The core product question is not whether Jev can produce scores. It is whether HireLens's criterion judgments meaningfully agree with well-defined human judgments and whether it improves candidate discovery compared with simpler approaches.

### Evaluation dataset

Build a representative corpus consisting of:

```text
roles
  x
resumes
  x
criterion-level human labels
```

Human labels should use the same explicit rubric levels used by the product.

Where practical, each example should be independently reviewed by more than one evaluator so human disagreement can be measured rather than hidden.

### Metrics

At minimum measure:

- criterion-level agreement,
- false-positive rate,
- false-negative rate,
- precision and recall for thresholded decisions,
- confidence calibration,
- performance by criterion category,
- performance by resume format/style,
- required-criterion miss rate,
- disagreement between human evaluators.

### Baselines

Jev should not be evaluated in isolation.

Compare against useful baselines such as:

- keyword overlap,
- lexical/BM25 retrieval,
- embedding similarity,
- general-purpose LLM scoring.

This allows HireLens to establish where Jev actually provides an advantage.

### Regression suite

Once labelled examples exist, they should become a versioned regression dataset.

Changes to:

- prompts,
- rubric definitions,
- Jev model versions,
- aggregation,
- preprocessing,
- resume extraction,

should be testable against the benchmark before being adopted.

## 9. Scoring and Decision Principles

### Aggregate score

Keep the weighted aggregate because it is operationally useful for ordering large candidate pools.

However:

- it is a projection of the criterion vector,
- it must not be presented as an objective measure of candidate quality,
- criterion-level information must remain accessible,
- required criteria should remain review signals rather than automatic rejection rules.

### Confidence

Score and confidence represent different things and must not be conflated.

A high score with low confidence should be visibly different from a high score with high confidence.

Low-confidence evaluations should encourage human inspection.

### Missing evidence

Absence of documented resume evidence is not evidence of absence of capability.

Product language and UI labels should consistently preserve this distinction.

## 10. Intended System Boundary

HireLens should optimize for being a semantic decision layer rather than expanding horizontally into every recruiting workflow.

Long term, the system boundary can look like:

```text
ATS / application source
        |
        v
     HireLens
        |
   Role rubric
        |
        v
 Jev evaluation
        |
        v
Semantic candidate space
        |
        v
Recruiter review
        |
        v
ATS / downstream workflow
```

This allows systems such as Greenhouse, Lever, Workday, or other applicant sources to remain systems of record while HireLens specializes in candidate evaluation and exploration.

## 11. Non-Goals

The following are explicitly not priorities for this improvement phase:

- interview scheduling,
- offer management,
- onboarding,
- HRIS functionality,
- payroll,
- automated email sending,
- calendar management,
- autonomous candidate rejection,
- autonomous hiring decisions,
- rebuilding a full ATS workflow.

Integrations with ATS products may become useful later, but they should feed the HireLens decision engine rather than redefine the product around ATS administration.

## 12. Implementation Sequence

Implement in this order:

1. JD-to-rubric generation with mandatory recruiter approval.
2. Candidate-by-criterion matrix.
3. Criterion-based semantic filtering.
4. Independent resume evidence retrieval.
5. Evaluation, calibration, baseline comparison, and regression tooling.

Evaluation work should begin as soon as representative examples are available rather than waiting for every product surface to be complete.

## 13. Product Thesis

HireLens should not compete on the claim that it uses AI to score resumes. That capability is increasingly common.

The differentiating model is:

> HireLens converts a hiring rubric into a semantic query over the applicant pool.

A job is represented as explicit evaluation dimensions.

A candidate is represented as a vector of criterion-level semantic judgments.

Jev makes those repeated structured judgments efficiently.

Recruiters can then rank, filter, compare, inspect evidence, and make their own decisions using structured information derived from otherwise unstructured resumes.

The result is not an AI hiring oracle. It is an inspectable decision-support system for reasoning about large candidate pools.
