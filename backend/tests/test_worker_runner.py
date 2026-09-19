import threading

from workers.runner import WorkerConfig, WorkerRunner


def test_worker_runner_stops_when_signaled() -> None:
    stop = threading.Event()
    iterations = {"count": 0}

    def loop(event: threading.Event) -> None:
        while not event.wait(0.01):
            iterations["count"] += 1
            if iterations["count"] >= 3:
                event.set()

    runner = WorkerRunner(WorkerConfig(name="test"), loop=loop)
    runner._stop = stop
    runner._loop(stop)

    assert iterations["count"] >= 1
