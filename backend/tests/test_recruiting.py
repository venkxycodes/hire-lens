import hashlib
from datetime import timedelta
from io import BytesIO
from unittest.mock import Mock

import httpx
import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client
from django.utils import timezone
from docx import Document
from rest_framework.test import APIClient

from recruiting.documents import extract_resume
from recruiting.evaluations import enqueue, process_one
from recruiting.models import Application, Evaluation, Job
from recruiting.scoring import ProviderError, build_request, evaluate_live, summarize

pytestmark = pytest.mark.django_db
CRITERIA = [
    {
        "id": "python",
        "name": "Python",
        "description": "Developing production Python APIs",
        "weight": 70,
        "required": True,
    },
    {
        "id": "ownership",
        "name": "Ownership",
        "description": "Owning outcomes",
        "weight": 30,
        "required": False,
    },
]
TEXT = "Alex Rivera\nalex@example.com\nBuilt Python and Django APIs and owned production outcomes."


@pytest.fixture
def user():
    return get_user_model().objects.create_user(username="recruiter", password="test-password")


@pytest.fixture
def client(user):
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def job(user):
    return Job.objects.create(
        owner=user, title="Backend Engineer", description="Build Python APIs", criteria=CRITERIA
    )


@pytest.fixture
def application(job):
    return Application.objects.create(
        job=job,
        name="Alex Rivera",
        resume_text=TEXT,
        content_hash=hashlib.sha256(TEXT.encode()).hexdigest(),
    )


def answers(score=3, confidence=0.9):
    return {
        c["id"]: {
            "type": "score",
            "score": score,
            "confidence": confidence,
            "probabilities": {str(i): float(i == score) for i in range(5)},
        }
        for c in CRITERIA
    }


def test_private_workspaces_and_unauthenticated_requests(client, job, application):
    assert APIClient().get("/api/v1/jobs/").status_code == 403
    other = get_user_model().objects.create_user(username="other")
    client.force_authenticate(other)
    assert client.get("/api/v1/jobs/").json() == []
    assert client.get(f"/api/v1/jobs/{job.pk}/").status_code == 404
    assert client.get(f"/api/v1/applications/{application.pk}/").status_code == 404
    assert (
        client.patch(
            f"/api/v1/applications/{application.pk}/", {"stage": "shortlisted"}
        ).status_code
        == 404
    )
    assert client.get(f"/api/v1/applications/{application.pk}/resume/").status_code == 404


def test_login_csrf_and_logout(user):
    client = Client(enforce_csrf_checks=True)
    session = client.get("/api/v1/session/").json()
    assert (
        client.post(
            "/api/v1/login/", {"username": user.username, "password": "test-password"}
        ).status_code
        == 403
    )
    login = client.post(
        "/api/v1/login/",
        {"username": user.username, "password": "test-password"},
        HTTP_X_CSRFTOKEN=session["csrf_token"],
    )
    assert login.status_code == 200
    assert client.get("/api/v1/jobs/").status_code == 200
    assert client.delete("/api/v1/session/").status_code == 403
    assert (
        client.delete("/api/v1/session/", HTTP_X_CSRFTOKEN=login.json()["csrf_token"]).status_code
        == 204
    )
    assert client.get("/api/v1/jobs/").status_code == 403


def test_criteria_validation_and_versioning(client, job):
    assert (
        client.patch(f"/api/v1/jobs/{job.pk}/", {"criteria": []}, format="json").status_code == 400
    )
    assert (
        client.patch(
            f"/api/v1/jobs/{job.pk}/", {"criteria": [CRITERIA[0], CRITERIA[0]]}, format="json"
        ).status_code
        == 400
    )
    invalid = [{**CRITERIA[0], "weight": 0}]
    assert (
        client.patch(f"/api/v1/jobs/{job.pk}/", {"criteria": invalid}, format="json").status_code
        == 400
    )
    assert client.patch(f"/api/v1/jobs/{job.pk}/", {"location": "Remote"}).json()["version"] == 1
    assert (
        client.patch(f"/api/v1/jobs/{job.pk}/", {"description": "New responsibilities"}).json()[
            "version"
        ]
        == 2
    )


def test_upload_partial_failure_and_duplicates(client, job, settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path
    response = client.post(
        f"/api/v1/jobs/{job.pk}/resumes/",
        {
            "files": [
                SimpleUploadedFile("alex.txt", TEXT.encode()),
                SimpleUploadedFile("bad.txt", b"tiny"),
                SimpleUploadedFile("bad.exe", b"invalid"),
            ]
        },
    )
    assert response.status_code == 201
    assert [r["status"] for r in response.json()["results"]] == ["added", "failed", "failed"]
    assert job.applications.count() == 1
    app = job.applications.get()
    assert app.email == "alex@example.com"
    assert client.get(f"/api/v1/applications/{app.pk}/resume/").status_code == 200
    response = client.post(
        f"/api/v1/jobs/{job.pk}/resumes/", {"name": "Alex", "resume_text": TEXT}, format="json"
    )
    assert response.json()["results"][0]["status"] == "duplicate"


def test_docx_extraction():
    doc = Document()
    doc.add_paragraph(TEXT)
    out = BytesIO()
    doc.save(out)
    assert "Python" in extract_resume(SimpleUploadedFile("alex.docx", out.getvalue()))
    with pytest.raises(ValueError, match="5 MB"):
        extract_resume(SimpleUploadedFile("large.txt", b"a" * (5 * 1024 * 1024 + 1)))


def test_idempotent_queue_and_weighted_score(job, application):
    assert enqueue(job.pk) == 1
    assert enqueue(job.pk) == 0
    provider_answers = answers()
    provider_answers["ownership"] = {
        "type": "score",
        "score": 1,
        "confidence": 0.7,
        "probabilities": {str(i): float(i == 1) for i in range(5)},
    }
    assert process_one(lambda *args: provider_answers)
    evaluation = Evaluation.objects.get()
    assert evaluation.status == "completed"
    assert evaluation.score == 60
    assert evaluation.confidence == 0.84
    assert application.stage == "new"
    assert not process_one()


def test_stale_scores_excluded_from_current_ranking(client, job, application):
    enqueue(job.pk)
    process_one(lambda *args: answers(4))
    assert client.get(f"/api/v1/applications/?job={job.pk}&min_score=75").json()["count"] == 1
    client.patch(f"/api/v1/jobs/{job.pk}/", {"description": "New job criteria"})
    assert client.get(f"/api/v1/applications/{application.pk}/").json()["stale"] is True
    assert client.get(f"/api/v1/applications/?job={job.pk}&min_score=75").json()["count"] == 0
    assert enqueue(job.pk) == 1
    assert Evaluation.objects.count() == 2
    old = Evaluation.objects.get(job_version=1)
    assert old.snapshot["description"] == "Build Python APIs"
    assert old.score == 100


@pytest.mark.parametrize(
    "bad",
    [
        {},
        {"python": {"type": "score"}},
        {
            c["id"]: {"type": "score", "score": float("nan"), "confidence": 1, "probabilities": {}}
            for c in CRITERIA
        },
    ],
)
def test_malformed_results_fail_without_zero_score(job, application, bad):
    enqueue(job.pk)
    process_one(lambda *args: bad)
    evaluation = Evaluation.objects.get()
    assert evaluation.status == "failed"
    assert evaluation.score is None
    assert enqueue(job.pk) == 1
    assert Evaluation.objects.count() == 1


def test_retry_and_expired_lease_recovery(job, application):
    enqueue(job.pk)

    def unavailable(*args):
        raise ProviderError("Temporarily unavailable", retryable=True)

    process_one(unavailable)
    e = Evaluation.objects.get()
    assert e.status == "queued" and e.attempts == 1
    assert not process_one()
    Evaluation.objects.update(status="running", lease_until=timezone.now() - timedelta(seconds=1))
    process_one(lambda *args: answers())
    e.refresh_from_db()
    assert e.status == "completed" and e.attempts == 2


def test_exhausted_lease_becomes_failure(job, application):
    enqueue(job.pk)
    Evaluation.objects.update(
        status="running", attempts=3, lease_until=timezone.now() - timedelta(seconds=1)
    )
    assert not process_one()
    assert Evaluation.objects.get().status == "failed"


def test_provider_contract_and_failure_sanitization(settings, monkeypatch):
    settings.JEV_API_KEY = "secret-not-for-browser"
    snapshot = {"description": "Job", "criteria": CRITERIA}
    request = build_request(snapshot, TEXT, "jev-1.13.0")
    assert set(request) == {"model", "state", "questions"}
    assert request["questions"]["python"]["type"] == "score"
    assert len(request["questions"]["python"]["criteria"]) == 5
    mock = Mock(return_value=httpx.Response(200, json={"answers": answers()}))
    monkeypatch.setattr(httpx, "post", mock)
    assert evaluate_live(snapshot, TEXT, "jev-1.13.0") == answers()
    assert mock.call_args.args[0] == "https://api.typesafe.ai/v1/systemone"
    mock.return_value = httpx.Response(429, text="secret-not-for-browser")
    with pytest.raises(ProviderError) as exc:
        evaluate_live(snapshot, TEXT, "jev-1.13.0")
    assert exc.value.retryable
    assert "secret" not in str(exc.value)


def test_score_distribution_validation():
    a = answers()
    a["python"]["probabilities"]["1"] = 1
    with pytest.raises(ProviderError):
        summarize(a, CRITERIA)
    a = answers()
    a["python"]["score"] = True
    with pytest.raises(ProviderError):
        summarize(a, CRITERIA)


def test_manual_stage_audit_and_filters(client, job, application):
    response = client.patch(
        f"/api/v1/applications/{application.pk}/",
        {"stage": "shortlisted", "notes": "Ask about deployment ownership"},
    )
    assert response.status_code == 200
    assert len(response.json()["activity"]) == 2
    assert (
        client.get(f"/api/v1/applications/?job={job.pk}&stage=shortlisted&search=alex").json()[
            "count"
        ]
        == 1
    )
    assert client.get("/api/v1/applications/?min_score=oops").status_code == 400
    assert client.get("/api/v1/applications/?min_score=NaN").status_code == 400


def test_missing_provider_key_and_foreign_selection(client, job, application, settings, user):
    settings.JEV_API_KEY = ""
    settings.JEV_MODE = "live"
    assert client.post(f"/api/v1/jobs/{job.pk}/evaluate/", {}, format="json").status_code == 503
    settings.JEV_MODE = "demo"
    assert (
        client.post(
            f"/api/v1/jobs/{job.pk}/evaluate/", {"application_ids": [999999]}, format="json"
        ).status_code
        == 400
    )
    assert (
        client.post(
            f"/api/v1/jobs/{job.pk}/evaluate/", {"application_ids": [application.pk]}, format="json"
        ).status_code
        == 202
    )
    process_one()
    assert Evaluation.objects.get().provider == "demo"


def test_closed_job_blocks_upload_and_evaluation(client, job, settings):
    settings.JEV_MODE = "demo"
    job.status = "closed"
    job.save()
    assert client.post(f"/api/v1/jobs/{job.pk}/evaluate/").status_code == 400
    assert (
        client.post(
            f"/api/v1/jobs/{job.pk}/resumes/", {"name": "Alex", "resume_text": TEXT}
        ).status_code
        == 400
    )


def test_notes_patch_preserves_evaluation_enqueued_after_read(user, job, application):
    from types import SimpleNamespace

    from recruiting.serializers import ApplicationDetailSerializer
    from recruiting.views import ApplicationViewSet

    stale = Application.objects.get(pk=application.pk)
    serializer = ApplicationDetailSerializer(stale, data={"notes": "New notes"}, partial=True)
    serializer.is_valid(raise_exception=True)
    enqueue(job.pk)
    Application.objects.filter(pk=application.pk).update(stage="shortlisted")
    view = ApplicationViewSet()
    view.request = SimpleNamespace(user=user)
    view.perform_update(serializer)
    application.refresh_from_db()
    assert application.latest_evaluation_id == Evaluation.objects.get().pk
    assert application.stage == "shortlisted"
    assert application.notes == "New notes"


def test_demo_to_live_creates_new_result_and_hides_demo(client, job, application, settings):
    settings.JEV_MODE = "demo"
    enqueue(job.pk)
    process_one()
    demo = Evaluation.objects.get()
    settings.JEV_MODE = "live"
    assert client.get(f"/api/v1/applications/{application.pk}/").json()["stale"]
    assert client.get(f"/api/v1/applications/?job={job.pk}&min_score=0").json()["count"] == 0
    assert enqueue(job.pk) == 1
    process_one(lambda *args: answers())
    application.refresh_from_db()
    assert application.latest_evaluation.provider == "live"
    assert Evaluation.objects.get(pk=demo.pk).provider == "demo"
    assert Evaluation.objects.count() == 2


def test_outreach_draft_persists_without_contacting(client, application):
    response = client.patch(
        f"/api/v1/applications/{application.pk}/",
        {
            "outreach_subject": "Let's talk",
            "outreach_body": "Your Python experience caught my attention.",
        },
    )
    assert response.status_code == 200
    data = client.get(f"/api/v1/applications/{application.pk}/").json()
    assert data["outreach_subject"] == "Let's talk"
    assert data["stage"] == "new"


def test_import_resume_folder_adds_pdfs_skips_duplicates_and_queues(job, tmp_path, settings, monkeypatch):
    settings.JEV_MODE = "demo"
    from recruiting.management.commands import import_resume_folder

    for filename in ("alex.pdf", "duplicate.pdf", "bad.pdf"):
        (tmp_path / filename).write_bytes(b"pdf")

    def fake_extract(handle):
        if handle.name.endswith("bad.pdf"):
            raise ValueError("Not enough readable text.")
        return TEXT

    monkeypatch.setattr(import_resume_folder, "extract_resume", fake_extract)
    call_command("import_resume_folder", "--job-id", str(job.pk), str(tmp_path))
    assert job.applications.count() == 1
    assert Evaluation.objects.filter(application__job=job, status="queued").count() == 1


def test_import_resume_folder_requires_pdf_corpus(job, tmp_path):
    from django.core.management import CommandError

    with pytest.raises(CommandError, match="No PDF"):
        call_command("import_resume_folder", "--job-id", str(job.pk), str(tmp_path))
