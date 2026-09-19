"""Import a local PDF corpus into a job and optionally queue evaluations."""

import hashlib
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from recruiting.documents import contact_from_text, extract_resume
from recruiting.evaluations import enqueue
from recruiting.models import Application, Job


class Command(BaseCommand):
    help = "Import PDF resumes from a local folder into a job."

    def add_arguments(self, parser):
        parser.add_argument("--job-id", type=int, required=True)
        parser.add_argument("folder", type=Path)
        parser.add_argument("--no-evaluate", action="store_true")
        parser.add_argument("--recursive", action="store_true")

    def handle(self, *args, **options):
        job = Job.objects.filter(pk=options["job_id"]).first()
        if job is None:
            raise CommandError(f"Job {options['job_id']} does not exist.")
        if job.status != "open":
            raise CommandError("The job is closed. Reopen it before importing resumes.")
        folder = options["folder"].expanduser().resolve()
        if not folder.is_dir():
            raise CommandError(f"Resume folder does not exist: {folder}")
        pattern = "**/*.pdf" if options["recursive"] else "*.pdf"
        files = sorted(path for path in folder.glob(pattern) if path.is_file())
        if not files:
            raise CommandError(f"No PDF resumes found in {folder}.")

        added = duplicates = failed = 0
        failures = []
        for path in files:
            try:
                with path.open("rb") as handle:
                    text = extract_resume(handle)
                name, email = contact_from_text(text, path.name)
                digest = hashlib.sha256(text.strip().encode()).hexdigest()
                with transaction.atomic():
                    application, created = Application.objects.get_or_create(
                        job=job,
                        content_hash=digest,
                        defaults={
                            "name": name,
                            "email": email,
                            "filename": path.name,
                            "resume_text": text,
                        },
                    )
                    if created:
                        with path.open("rb") as handle:
                            application.resume.save(path.name, handle)
                        added += 1
                    else:
                        duplicates += 1
            except (OSError, ValueError) as exc:
                failed += 1
                failures.append(f"{path.name}: {exc}")

        queued = 0 if options["no_evaluate"] else enqueue(job.pk)
        self.stdout.write(self.style.SUCCESS(
            f"Imported {added} new resumes, skipped {duplicates} duplicates, "
            f"and failed {failed}. Queued {queued} evaluations for Job-{job.pk}."
        ))
        if failures:
            self.stdout.write("Failures:")
            for failure in failures:
                self.stdout.write(f"  {failure}")
