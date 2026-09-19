import hashlib
import re
from pathlib import Path

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.db.models import Count, F, Q
from django.http import FileResponse
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
from .models import Activity, Application, Job
from .scoring import PROMPT_VERSION
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



class CompareResumeView(APIView):
    """Compare one uploaded resume with one JD without requiring a Job or Jev setup."""

    def get_permissions(self):
        # Listing filenames is needed before the recruiter has a session; scoring remains protected.
        if self.request.method == "GET":
            return [AllowAny()]
        return super().get_permissions()

    def get(self, request):
        root = Path(settings.BASE_DIR) / "data" / "resumes"
        root.mkdir(parents=True, exist_ok=True)
        return Response({"resumes": sorted(p.name for p in root.glob("*.pdf") if p.is_file())})

    def post(self, request):
        description = str(request.data.get("job_description", "")).strip()
        criteria_text = str(request.data.get("criteria", "")).strip()
        upload = request.FILES.get("resume")
        existing = str(request.data.get("resume_name", "")).strip()
        if len(description) < 40:
            return Response({"detail": "Paste a job description with at least 40 characters."}, status=400)
        root = Path(settings.BASE_DIR) / "data" / "resumes"
        root.mkdir(parents=True, exist_ok=True)
        if existing and not upload:
            candidate = root / Path(existing).name
            if candidate.parent != root or not candidate.is_file():
                return Response({"detail": "That saved resume was not found."}, status=404)
            upload = open(candidate, "rb")
            upload.name = candidate.name
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
        stop = {"and", "the", "with", "for", "that", "this", "from", "are", "you", "your", "our", "have", "will", "job", "role"}
        criteria = [line.strip() for line in criteria_text.splitlines() if line.strip()]
        terms = {w for w in re.findall(r"[a-z][a-z+#.]{2,}", (description + " " + " ".join(criteria)).lower()) if w not in stop}
        resume_terms = set(re.findall(r"[a-z][a-z+#.]{2,}", resume_text.lower()))
        matched = sorted(terms & resume_terms)
        score = round(100 * len(matched) / max(1, len(terms)), 1)
        verdict = "Good match" if score >= 90 else "Average match" if score >= 70 else "No match"
        detail = (f"Matched {len(matched)} of {len(terms)} signals" + (f" across {len(criteria)} criteria." if criteria else "."))
        return Response({"filename": target.name, "score": score, "verdict": verdict, "detail": detail, "matched_terms": matched, "resume_name": contact_from_text(resume_text, target.name)[0]})


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
