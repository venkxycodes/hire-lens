import hashlib
import json
import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.db.models import Count, F, Q
from django.http import FileResponse
import httpx
from django.core.files import File
from django.middleware.csrf import get_token
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .documents import contact_from_text, extract_resume
from .evaluations import enqueue
from .models import Activity, Application, Job, ResumeScoringRun
from .scoring import PROMPT_VERSION, ProviderError, evaluate_live, summarize
from .serializers import (
    ApplicationDetailSerializer,
    ApplicationSerializer,
    JobSerializer,
    TextResumeSerializer,
)


class LoginThrottle(AnonRateThrottle):
    rate = "10/minute"


class SessionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "user": request.user.username if request.user.is_authenticated else None,
                "csrf_token": get_token(request),
                "mode": settings.JEV_MODE,
                "jev_configured": bool(settings.JEV_API_KEY),
            }
        )

    @method_decorator(csrf_protect)
    def delete(self, request):
        logout(request)
        return Response(status=204)


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]

    @method_decorator(csrf_protect)
    def post(self, request):
        user = authenticate(
            request,
            username=request.data.get("username", ""),
            password=request.data.get("password", ""),
        )
        if user is None:
            return Response({"detail": "Incorrect username or password."}, status=400)
        login(request, user)
        return Response(
            {
                "user": user.username,
                "csrf_token": get_token(request),
                "mode": settings.JEV_MODE,
                "jev_configured": bool(settings.JEV_API_KEY),
            }
        )



class RubricDraftView(APIView):
    def post(self, request):
        description = str(request.data.get("description", "")).strip()
        if len(description) < 80:
            return Response({"detail": "Add a fuller job description before drafting criteria."}, status=400)
        if settings.OPENROUTER_API_KEY:
            prompt = """Convert this job description into an editable hiring rubric. Return ONLY a JSON object with a criteria array. Each item must have id, name, description, category (eligibility/core_capability/technology/domain_experience/preferred/behavioral), priority (must_have/strong_signal/nice_to_have), weight (integer), required (boolean), rationale, and evidence_examples (array of strings). Use observable job evidence, separate must-haves from preferences, ignore demographic traits, and do not invent requirements. Normalize equivalent technologies, frameworks, tools, and terminology by capability and category rather than exact keyword matching. Treat named technologies as examples when the JD says “or similar”; preserve distinctions when they change the job's core capability. Put the equivalence guidance in the criterion description so Jev evaluates capability, while retaining any exact technology requirement as a separate criterion when it is genuinely required.

JOB DESCRIPTION:
""" + description
            try:
                response = httpx.post("https://openrouter.ai/api/v1/chat/completions", headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}", "Content-Type": "application/json", "HTTP-Referer": "https://hire-lens.local", "X-Title": "HireLens"}, json={"model": settings.OPENROUTER_MODEL, "temperature": 0.1, "response_format": {"type": "json_object"}, "messages": [{"role": "user", "content": prompt}]}, timeout=45)
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                draft = json.loads(content)
                criteria = draft.get("criteria")
                if isinstance(criteria, list) and criteria:
                    return Response({"criteria": criteria[:12], "provider": "openrouter", "model": settings.OPENROUTER_MODEL})
            except (httpx.HTTPError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                pass
        sentences = [part.strip(" .:-") for part in re.split(r"[\n.!?;]+", description) if len(part.strip()) >= 18][:8]
        weights = max(1, 100 // max(1, len(sentences)))
        criteria = [{"id": re.sub(r"[^a-z0-9]+", "-", item.lower()).strip("-")[:60] or f"criterion-{i}", "name": item[:100], "description": f"Evidence of {item[0].lower() + item[1:]}", "weight": weights, "required": i < 2} for i, item in enumerate(sentences)]
        if criteria: criteria[-1]["weight"] += 100 - sum(c["weight"] for c in criteria)
        return Response({"criteria": criteria, "provider": "heuristic-fallback", "failure_reason": "OpenRouter was unavailable or returned an invalid rubric; heuristic criteria were generated."})


class CompareResumeView(APIView):
    """Compare one uploaded resume with one JD without requiring a Job or Jev setup."""

    def get_permissions(self):
        # Listing filenames is needed before the recruiter has a session; scoring remains protected.
        if self.request.method == "GET":
            return [AllowAny()]
        return super().get_permissions()

    def get(self, request):
        root = Path(settings.BASE_DIR).parent / "data" / "resumes"
        root.mkdir(parents=True, exist_ok=True)
        return Response({"resumes": sorted(p.name for p in root.glob("*.pdf") if p.is_file())})

    def post(self, request):
        description = str(request.data.get("job_description", "")).strip()
        criteria_text = str(request.data.get("criteria", "")).strip()
        upload = request.FILES.get("resume")
        existing = str(request.data.get("resume_name", "")).strip()
        if len(description) < 40:
            return Response({"detail": "Paste a job description with at least 40 characters."}, status=400)
        root = Path(settings.BASE_DIR).parent / "data" / "resumes"
        root.mkdir(parents=True, exist_ok=True)
        if existing and not upload:
            candidate = root / Path(existing).name
            if candidate.parent != root or not candidate.is_file():
                return Response({"detail": "That saved resume was not found."}, status=404)
            upload = File(candidate.open("rb"), name=candidate.name)
        if not upload or not upload.name.lower().endswith(".pdf"):
            return Response({"detail": "Choose a saved PDF or upload one."}, status=400)
        try:
            resume_text = extract_resume(upload)
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=400)
        safe_name = Path(upload.name).name
        target = root / safe_name
        if target.exists():
            target = root / f"{Path(safe_name).stem}-{hashlib.sha256(resume_text.encode()).hexdigest()[:8]}.pdf"
        upload.seek(0)
        target.write_bytes(upload.read())
        criteria = [line.strip() for line in criteria_text.splitlines() if line.strip()]
        if not criteria:
            return Response({"detail": "Add at least one comparison criterion."}, status=400)
        rubric = [{"id": f"criterion_{i}", "name": item[:120], "description": item, "weight": 1, "required": False} for i, item in enumerate(criteria)]
        snapshot = {"description": description, "criteria": rubric}
        try:
            answers = evaluate_live(snapshot, resume_text, settings.JEV_MODEL)
            score, confidence, results = summarize(answers, rubric)
        except ProviderError as exc:
            return Response({"detail": str(exc)}, status=503)
        verdict = "Good match" if score >= 90 else "Average match" if score >= 70 else "No match"
        run = ResumeScoringRun.objects.create(owner=request.user, job_description=description, criteria=rubric, resume_filename=target.name, score=score, verdict=verdict, results=results, reasoning=[f"{item['name']}: Jev score {round(item['score'])}/100." for item in results], metadata={"rubric_provider": request.data.get("rubric_provider", "unknown"), "rubric_failure_reason": request.data.get("rubric_failure_reason", "")})
        return Response({"id": run.id, "filename": target.name, "score": score, "verdict": verdict, "detail": f"Jev evaluated {len(results)} comparison criteria.", "criteria_results": results, "reasoning": run.reasoning, "resume_name": contact_from_text(resume_text, target.name)[0]})


class Pages(PageNumberPagination):
    page_size = 40


class JobViewSet(viewsets.ModelViewSet):
    serializer_class = JobSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return (
            Job.objects.filter(owner=self.request.user)
            .annotate(
                candidate_count=Count("applications", distinct=True),
                shortlisted_count=Count(
                    "applications", filter=Q(applications__stage="shortlisted"), distinct=True
                ),
                pending_count=Count(
                    "applications",
                    filter=Q(applications__latest_evaluation__status__in=["queued", "running"]),
                    distinct=True,
                ),
            )
            .order_by("-created_at")
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        job = get_object_or_404(
            Job.objects.select_for_update(), pk=kwargs["pk"], owner=request.user
        )
        serializer = self.get_serializer(job, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        changed = any(
            key in serializer.validated_data and serializer.validated_data[key] != getattr(job, key)
            for key in ("description", "criteria", "title")
        )
        serializer.save(version=job.version + int(changed))
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def resumes(self, request, pk=None):
        job = self.get_object()
        if job.status != "open":
            return Response({"detail": "Reopen this job before adding resumes."}, status=400)
        files = request.FILES.getlist("files")
        outcomes = []
        if files:
            if len(files) > 20:
                return Response({"detail": "Upload at most 20 files per batch."}, status=400)
            for upload in files:
                try:
                    text = extract_resume(upload)
                    name, email = contact_from_text(text, upload.name)
                    application, created = self._add_resume(job, name, email, text, upload)
                    outcomes.append(
                        {
                            "filename": upload.name,
                            "id": application.pk,
                            "status": "added" if created else "duplicate",
                        }
                    )
                except ValueError as exc:
                    outcomes.append(
                        {"filename": upload.name, "status": "failed", "error": str(exc)}
                    )
        else:
            serializer = TextResumeSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            data = serializer.validated_data
            application, created = self._add_resume(
                job, data["name"], data.get("email", ""), data["resume_text"]
            )
            outcomes.append(
                {
                    "id": application.pk,
                    "status": "added" if created else "duplicate",
                    "filename": application.name,
                }
            )
        return Response({"results": outcomes}, status=status.HTTP_201_CREATED)

    def _add_resume(self, job, name, email, text, upload=None):
        digest = hashlib.sha256(text.strip().encode()).hexdigest()
        with transaction.atomic():
            # Serialize duplicate intake with evaluation and rubric changes for this job.
            Job.objects.select_for_update().get(pk=job.pk)
            application, created = Application.objects.get_or_create(
                job=job,
                content_hash=digest,
                defaults={
                    "name": name,
                    "email": email,
                    "resume_text": text,
                    "filename": upload.name if upload else "Pasted resume",
                },
            )
            if created and upload:
                application.resume.save(upload.name, upload)
        return application, created

    @action(detail=True, methods=["get"], url_path="top-candidates")
    def top_candidates(self, request, pk=None):
        job = self.get_object()
        try:
            limit = min(max(int(request.query_params.get("limit", 10)), 1), 100)
        except ValueError:
            return Response({"detail": "limit must be a number between 1 and 100."}, status=400)
        current = Q(latest_evaluation__job_version=F("job__version"), latest_evaluation__status="completed", latest_evaluation__provider=settings.JEV_MODE, latest_evaluation__model=settings.JEV_MODEL, latest_evaluation__prompt_version=PROMPT_VERSION)
        candidates = Application.objects.filter(job=job).filter(current).select_related("latest_evaluation").order_by("-latest_evaluation__score", "id")[:limit]
        return Response({"job": job.pk, "limit": limit, "results": ApplicationSerializer(candidates, many=True).data})

    @action(detail=True, methods=["post"])
    def evaluate(self, request, pk=None):
        job = self.get_object()
        if job.status != "open":
            return Response({"detail": "Reopen this job before evaluating."}, status=400)
        if settings.JEV_MODE != "demo" and not settings.JEV_API_KEY:
            return Response(
                {
                    "detail": "Set JEV_API_KEY on the server before evaluating, or explicitly enable JEV_MODE=demo."
                },
                status=503,
            )
        ids = request.data.get("application_ids")
        if ids is not None:
            field = serializers.ListField(
                child=serializers.IntegerField(min_value=1), allow_empty=False, max_length=1000
            )
            ids = field.run_validation(ids)
            if job.applications.filter(id__in=ids).count() != len(set(ids)):
                return Response(
                    {"detail": "One or more candidates do not belong to this job."}, status=400
                )
        return Response({"queued": enqueue(job.pk, ids)}, status=202)


class ApplicationViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "patch", "head", "options"]
    pagination_class = Pages

    def get_serializer_class(self):
        return ApplicationSerializer if self.action == "list" else ApplicationDetailSerializer

    def get_queryset(self):
        qs = Application.objects.filter(job__owner=self.request.user).select_related(
            "job", "latest_evaluation"
        )
        if self.action != "list":
            return qs
        params = self.request.query_params
        if params.get("job"):
            try:
                qs = qs.filter(job_id=int(params["job"]))
            except ValueError:
                raise serializers.ValidationError({"job": "Expected a job ID."})
        if params.get("search"):
            qs = qs.filter(
                Q(name__icontains=params["search"]) | Q(email__icontains=params["search"])
            )
        if params.get("stage"):
            qs = qs.filter(stage=params["stage"])
        current = Q(
            latest_evaluation__job_version=F("job__version"),
            latest_evaluation__provider=settings.JEV_MODE,
            latest_evaluation__model=settings.JEV_MODEL,
            latest_evaluation__prompt_version=PROMPT_VERSION,
        )
        if params.get("evaluation") == "stale":
            qs = qs.filter(latest_evaluation__isnull=False).exclude(current)
        elif params.get("evaluation"):
            qs = qs.filter(current, latest_evaluation__status=params["evaluation"])
        if params.get("min_score"):
            try:
                minimum = float(params["min_score"])
                if not 0 <= minimum <= 100:
                    raise ValueError
            except ValueError:
                raise serializers.ValidationError({"min_score": "Use a score between 0 and 100."})
            qs = qs.filter(
                current,
                latest_evaluation__status="completed",
                latest_evaluation__score__gte=minimum,
            )
        from django.db.models import Case, FloatField, When

        qs = qs.annotate(
            current_score=Case(
                When(
                    current & Q(latest_evaluation__status="completed"),
                    then=F("latest_evaluation__score"),
                ),
                default=None,
                output_field=FloatField(),
            )
        )
        ordering = params.get("ordering", "score")
        if ordering == "name":
            return qs.order_by("name", "id")
        if ordering == "newest":
            return qs.order_by("-id")
        return qs.order_by(F("current_score").desc(nulls_last=True), "id")

    @transaction.atomic
    def perform_update(self, serializer):
        old = Application.objects.select_for_update().get(pk=serializer.instance.pk)
        old_stage, old_notes = old.stage, old.notes
        serializer.instance = old
        updated = serializer.save()
        if old_stage != updated.stage:
            Activity.objects.create(
                application=updated,
                actor=self.request.user,
                message=f"Moved from {old_stage} to {updated.stage}.",
            )
        if old_notes != updated.notes:
            Activity.objects.create(
                application=updated, actor=self.request.user, message="Recruiter notes updated."
            )

    @action(detail=True, methods=["get"])
    def resume(self, request, pk=None):
        application = self.get_object()
        if not application.resume:
            return Response({"detail": "This resume was pasted as text."}, status=404)
        return FileResponse(
            application.resume.open("rb"), as_attachment=True, filename=application.filename
        )
