"""Create illustrative data without calling Jev or modifying an existing account."""

import hashlib
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from recruiting.evaluations import enqueue
from recruiting.models import Application, Evaluation, Job
from recruiting.scoring import evaluate_demo, summarize


class Command(BaseCommand):
    help = "Add demo roles and fictional resumes. Requires JEV_MODE=demo."

    def add_arguments(self, parser):
        parser.add_argument("--username", default="demo")

    def handle(self, *args, **options):
        if settings.JEV_MODE != "demo":
            raise CommandError("Set JEV_MODE=demo to create illustrative data.")
        user = get_user_model().objects.filter(username=options["username"]).first()
        if user is None:
            password = os.environ.get("DEMO_PASSWORD")
            if not password or len(password) < 10:
                raise CommandError(
                    "Set DEMO_PASSWORD (at least 10 characters) for a new demo account."
                )
            user = get_user_model().objects.create_user(options["username"], password=password)
        criteria = [
            {
                "id": "python",
                "name": "Python & Django",
                "description": "Python Django REST APIs PostgreSQL testing",
                "weight": 45,
                "required": True,
            },
            {
                "id": "systems",
                "name": "Production systems",
                "description": "Production reliability monitoring deployment scaling",
                "weight": 35,
                "required": True,
            },
            {
                "id": "ownership",
                "name": "Ownership & collaboration",
                "description": "Ownership mentoring collaboration product outcomes",
                "weight": 20,
                "required": False,
            },
        ]
        job, _ = Job.objects.get_or_create(
            owner=user,
            title="Senior Backend Engineer",
            defaults={
                "department": "Engineering",
                "location": "Remote · US",
                "description": "Build reliable Python and Django REST APIs. Own PostgreSQL data models, testing, production deployment and monitoring. Collaborate with product and mentor engineers. Demonstrate measurable outcomes and thoughtful system design.",
                "criteria": criteria,
            },
        )
        people = [
            (
                "Alex Rivera",
                "Built Python Django REST APIs with PostgreSQL and automated testing. Owned production reliability, monitoring, deployment and scaling. Led mentoring and product collaboration with ownership of measurable outcomes.",
                "shortlisted",
            ),
            (
                "Jordan Lee",
                "Developed Python Django APIs using PostgreSQL. Led testing and production deployment. Worked with product teams on reliable integrations and monitoring.",
                "new",
            ),
            (
                "Samira Patel",
                "Software engineer focused on Python Django REST APIs and PostgreSQL testing. Delivered backend integrations and collaborated with frontend engineers.",
                "new",
            ),
            (
                "Casey Morgan",
                "Platform engineer owning production reliability, monitoring, deployment and scaling. Python automation and infrastructure systems. Led mentoring and collaboration across product teams.",
                "hold",
            ),
            (
                "Taylor Chen",
                "Frontend developer building React TypeScript user interfaces. Collaborated with design and product partners. Used Python scripting for analysis and internal tools.",
                "new",
            ),
            (
                "Morgan Brooks",
                "Backend engineer developing Python REST APIs. Experience in database migrations and testing. Contributed to monitoring tools and product collaboration.",
                "contacted",
            ),
        ]
        for name, body, stage in people:
            email = name.lower().replace(" ", ".") + "@example.com"
            text = f"{name}\n{email}\n\nProfessional experience\n{body}\n\nThis is a fictional resume for demonstration."
            Application.objects.get_or_create(
                job=job,
                content_hash=hashlib.sha256(text.encode()).hexdigest(),
                defaults={
                    "name": name,
                    "email": email,
                    "filename": "Pasted resume",
                    "resume_text": text,
                    "stage": stage,
                },
            )
        Job.objects.get_or_create(
            owner=user,
            title="Product Designer",
            defaults={
                "department": "Design",
                "location": "Hybrid · San Francisco",
                "description": "Design accessible product experiences through user research, prototyping, and close engineering collaboration.",
                "criteria": [
                    {
                        "id": "design",
                        "name": "Product design",
                        "description": "User research prototyping accessibility product design",
                        "weight": 100,
                        "required": True,
                    }
                ],
            },
        )
        enqueue(job.pk)
        for evaluation in Evaluation.objects.filter(
            application__job=job, provider="demo", status="queued"
        ):
            answers = evaluate_demo(
                evaluation.snapshot, evaluation.application.resume_text, evaluation.model
            )
            score, confidence, results = summarize(answers, evaluation.snapshot["criteria"])
            evaluation.score, evaluation.confidence, evaluation.results = score, confidence, results
            evaluation.status, evaluation.completed_at = "completed", timezone.now()
            evaluation.save()
        self.stdout.write(
            self.style.SUCCESS(
                f"Demo workspace ready for {user.username}. No live Jev calls made for these demo evaluations."
            )
        )
