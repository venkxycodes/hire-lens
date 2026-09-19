from django.conf import settings
from rest_framework import serializers

from .models import Application, Evaluation, Job
from .scoring import PROMPT_VERSION


class CriterionSerializer(serializers.Serializer):
    id = serializers.SlugField(max_length=60)
    name = serializers.CharField(max_length=100)
    description = serializers.CharField(max_length=1000)
    weight = serializers.IntegerField(min_value=1, max_value=100)
    required = serializers.BooleanField(default=False)


class JobSerializer(serializers.ModelSerializer):
    criteria = CriterionSerializer(many=True, allow_empty=False)
    candidate_count = serializers.IntegerField(read_only=True)
    shortlisted_count = serializers.IntegerField(read_only=True)
    pending_count = serializers.IntegerField(read_only=True)
    description = serializers.CharField(max_length=20000)

    class Meta:
        model = Job
        fields = [
            "id",
            "title",
            "department",
            "location",
            "description",
            "criteria",
            "version",
            "status",
            "candidate_count",
            "shortlisted_count",
            "pending_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["version", "created_at", "updated_at"]

    def validate_criteria(self, value):
        if len(value) > 12:
            raise serializers.ValidationError("Use at most 12 focused criteria.")
        if len({c["id"] for c in value}) != len(value):
            raise serializers.ValidationError("Criterion IDs must be unique.")
        return value


class EvaluationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Evaluation
        fields = [
            "id",
            "job_version",
            "status",
            "provider",
            "model",
            "score",
            "confidence",
            "results",
            "error",
            "attempts",
            "completed_at",
        ]


class ApplicationSerializer(serializers.ModelSerializer):
    evaluation = EvaluationSerializer(source="latest_evaluation", read_only=True)
    stale = serializers.SerializerMethodField()

    class Meta:
        model = Application
        fields = [
            "id",
            "job",
            "name",
            "email",
            "filename",
            "stage",
            "notes",
            "outreach_subject",
            "outreach_body",
            "evaluation",
            "stale",
            "created_at",
        ]
        read_only_fields = ["job", "filename", "created_at"]
        extra_kwargs = {"notes": {"max_length": 20000}, "outreach_body": {"max_length": 20000}}

    def get_stale(self, obj):
        return bool(
            obj.latest_evaluation
            and (
                obj.latest_evaluation.job_version != obj.job.version
                or obj.latest_evaluation.provider != settings.JEV_MODE
                or obj.latest_evaluation.model != settings.JEV_MODEL
                or obj.latest_evaluation.prompt_version != PROMPT_VERSION
            )
        )


class ApplicationDetailSerializer(ApplicationSerializer):
    history = EvaluationSerializer(source="evaluations", many=True, read_only=True)
    activity = serializers.SerializerMethodField()

    class Meta(ApplicationSerializer.Meta):
        fields = ApplicationSerializer.Meta.fields + ["resume_text", "history", "activity"]
        read_only_fields = ApplicationSerializer.Meta.read_only_fields + ["resume_text"]

    def get_activity(self, obj):
        return list(obj.activity.order_by("-created_at").values("message", "created_at")[:30])


class TextResumeSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=160)
    email = serializers.EmailField(required=False, allow_blank=True)
    resume_text = serializers.CharField(min_length=40, max_length=40000)
