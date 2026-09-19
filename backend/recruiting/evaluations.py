import logging
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import DatabaseError, close_old_connections, transaction
from django.db.models import F, Q
from django.utils import timezone

from .models import Application, Evaluation, Job
from .scoring import PROMPT_VERSION, ProviderError, evaluate_demo, evaluate_live, summarize

logger = logging.getLogger(__name__)
MAX_ATTEMPTS = 3


@transaction.atomic
def enqueue(job_id, application_ids=None):
    job = Job.objects.select_for_update().get(pk=job_id)
    applications = job.applications.all()
    if application_ids is not None:
        applications = applications.filter(id__in=application_ids)
    queued = 0
    for application in applications.iterator():
        evaluation, created = Evaluation.objects.get_or_create(
            application=application,
            job_version=job.version,
            provider=settings.JEV_MODE,
            model=settings.JEV_MODEL,
            prompt_version=PROMPT_VERSION,
            defaults={
                "snapshot": {
                    "title": job.title,
                    "description": job.description,
                    "criteria": job.criteria,
                    "prompt_version": PROMPT_VERSION,
                },
                "available_at": timezone.now(),
            },
        )
        if evaluation.status == "failed":
            evaluation.status, evaluation.error, evaluation.attempts = "queued", "", 0
            evaluation.available_at = timezone.now()
            evaluation.provider, evaluation.model = settings.JEV_MODE, settings.JEV_MODEL
            evaluation.save()
            queued += 1
        elif created:
            queued += 1
        Application.objects.filter(pk=application.pk).update(latest_evaluation=evaluation)
    return queued


def process_one(evaluator=None):
    now = timezone.now()
    eligible = Q(status="queued", available_at__lte=now) | Q(status="running", lease_until__lt=now)
    # An expired third attempt is terminal even if its worker died mid-request.
    Evaluation.objects.filter(eligible, attempts__gte=MAX_ATTEMPTS).update(
        status="failed",
        error="Evaluation interrupted repeatedly. Please retry.",
        lease_token=None,
        lease_until=None,
    )
    candidate = (
        Evaluation.objects.filter(eligible, attempts__lt=MAX_ATTEMPTS)
        .order_by("available_at", "id")
        .first()
    )
    if candidate is None:
        return False
    token = uuid.uuid4()
    claimed = (
        Evaluation.objects.filter(pk=candidate.pk)
        .filter(eligible)
        .update(
            status="running",
            lease_token=token,
            lease_until=now + timedelta(minutes=2),
            attempts=F("attempts") + 1,
        )
    )
    if not claimed:
        return True
    candidate.refresh_from_db()
    owned = Evaluation.objects.filter(pk=candidate.pk, lease_token=token, status="running")
    try:
        provider = evaluator or (evaluate_demo if candidate.provider == "demo" else evaluate_live)
        answers = provider(candidate.snapshot, candidate.application.resume_text, candidate.model)
        score, confidence, results = summarize(answers, candidate.snapshot["criteria"])
        owned.update(
            status="completed",
            score=score,
            confidence=confidence,
            results=results,
            completed_at=timezone.now(),
            error="",
            lease_token=None,
            lease_until=None,
        )
    except ProviderError as exc:
        retry = exc.retryable and candidate.attempts < MAX_ATTEMPTS
        owned.update(
            status="queued" if retry else "failed",
            error=str(exc),
            available_at=timezone.now() + timedelta(seconds=10 * 2**candidate.attempts),
            lease_token=None,
            lease_until=None,
        )
    except Exception:
        logger.exception("Evaluation %s failed", candidate.pk)
        owned.update(
            status="failed",
            error="Evaluation failed unexpectedly. Please retry or contact your administrator.",
            lease_token=None,
            lease_until=None,
        )
    return True


def worker_loop(stop):
    while not stop.is_set():
        try:
            if not process_one():
                stop.wait(1)
        except DatabaseError:
            logger.exception("Database unavailable; retrying worker in five seconds")
            close_old_connections()
            stop.wait(5)
