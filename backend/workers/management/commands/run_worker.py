from django.core.management.base import BaseCommand

from workers.runner import WorkerConfig, WorkerRunner
from recruiting.evaluations import worker_loop


class Command(BaseCommand):
    help = "Run a background worker process until SIGTERM or SIGINT."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--name",
            default="default",
            help="Logical worker name (used in logs and process identity).",
        )
        parser.add_argument(
            "--poll-interval",
            type=float,
            default=1.0,
            help="Seconds between idle loop iterations.",
        )

    def handle(self, *args, **options) -> None:
        config = WorkerConfig(
            name=options["name"],
            poll_interval_seconds=options["poll_interval"],
        )
        WorkerRunner(config, loop=worker_loop).run()
