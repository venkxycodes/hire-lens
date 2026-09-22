import uuid

from django.conf import settings
from django.db import models


class Job(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=160)
    department = models.CharField(max_length=120, blank=True)
    location = models.CharField(max_length=120, blank=True)
    description = models.TextField()
    criteria = models.JSONField(default=list)
    version = models.PositiveIntegerField(default=1)
    status = models.CharField(
        max_length=12, choices=[("open", "Open"), ("closed", "Closed")], default="open"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


def resume_path(instance, filename):
    return f"resumes/{instance.job.owner_id}/{uuid.uuid4().hex}/{filename}"


class Application(models.Model):
    STAGES = [(s, s.title()) for s in ("new", "shortlisted", "hold", "rejected", "contacted")]
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    name = models.CharField(max_length=160)
    email = models.EmailField(blank=True)
    filename = models.CharField(max_length=255, blank=True)
    resume = models.FileField(upload_to=resume_path, blank=True, max_length=500)
    resume_text = models.TextField()
    content_hash = models.CharField(max_length=64)
    stage = models.CharField(max_length=20, choices=STAGES, default="new")
    notes = models.TextField(blank=True)
    outreach_subject = models.CharField(max_length=300, blank=True)
    outreach_body = models.TextField(blank=True)
    latest_evaluation = models.ForeignKey(
        "Evaluation", null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["job", "content_hash"], name="unique_resume_per_job")
        ]
        indexes = [models.Index(fields=["job", "stage", "id"])]


class Evaluation(models.Model):
    application = models.ForeignKey(
        Application, on_delete=models.CASCADE, related_name="evaluations"
    )
    job_version = models.PositiveIntegerField()
    snapshot = models.JSONField()
    status = models.CharField(max_length=12, default="queued", db_index=True)
    provider = models.CharField(max_length=20)
    model = models.CharField(max_length=80)
    prompt_version = models.CharField(max_length=40, default="resume-fit-v1")
    score = models.FloatField(null=True)
    confidence = models.FloatField(null=True)
    results = models.JSONField(default=list)
    error = models.CharField(max_length=300, blank=True)
    attempts = models.PositiveIntegerField(default=0)
    available_at = models.DateTimeField()
    lease_token = models.UUIDField(null=True)
    lease_until = models.DateTimeField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["application", "job_version", "provider", "model", "prompt_version"],
                name="unique_evaluation_version",
            )
        ]


class Activity(models.Model):
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name="activity")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    message = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)


class ResumeScoringRun(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="compare_runs")
    job_description = models.TextField()
    criteria = models.JSONField(default=list)
    resume_filename = models.CharField(max_length=255)
    score = models.FloatField()
    verdict = models.CharField(max_length=30)
    results = models.JSONField(default=list)
    reasoning = models.JSONField(default=list)
    rubric_provider = models.CharField(max_length=40, default="unknown")
    rubric_failure_reason = models.CharField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class TopCandidatesRun(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="top_candidates_runs")
    job_description = models.TextField()
    criteria = models.JSONField(default=list)
    corpus_path = models.CharField(max_length=500, blank=True)
    resume_count = models.PositiveIntegerField(default=0)
    results = models.JSONField(default=list)
    status = models.CharField(max_length=20, default="completed")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
