import logging
import time

import prometheus_client  # type: ignore

from celery.signals import (  # type: ignore
    after_task_publish,
    beat_init,
    before_task_publish,
    task_postrun,
    task_prerun,
    worker_ready,
)

from .metrics import (
    TASK_EXECUTION_TIME,
    TASK_POSTRUN,
    TASK_PRERUN,
    TASK_PUBLISHED,
    TASK_QUEUE_TIME,
)
from .thread_collector import CeleryThreadPoolCollector


try:
    from celery.concurrency.thread import TaskPool as ThreadTaskPool  # type: ignore
except ImportError:
    ThreadTaskPool = None


log = logging.getLogger(__name__)


class CeleryExporter:
    @classmethod
    def install(cls):
        if hasattr(cls, "_instance"):
            return
        self = cls()
        # Make sure to keep a reference alive so this is not garbage collected.
        cls._instance = self

        worker_ready.connect(self.on_worker_ready)
        beat_init.connect(self.on_beat_init)
        before_task_publish.connect(self.on_before_task_publish)
        after_task_publish.connect(self.on_after_task_publish)

    def on_worker_ready(self, sender, **_kwargs):
        task_prerun.connect(self.on_task_prerun)
        task_postrun.connect(self.on_task_postrun)

        # TODO Similar metrics for other pool implementations.
        if ThreadTaskPool and isinstance(sender.pool, ThreadTaskPool):
            collector = CeleryThreadPoolCollector(sender.pool.executor)
            prometheus_client.REGISTRY.register(collector)

        prometheus_client.start_http_server(9000)
        log.info("Prometheus exporter started for Celery worker on :9000")

    def on_beat_init(self, **_kwargs):
        prometheus_client.start_http_server(9000)
        log.info("Prometheus exporter started for Celery beat on :9000")

    def on_before_task_publish(self, headers, **_kwargs):
        # Sorry, not handling leap seconds, your metrics might be off by
        # 1 second during a leap second.
        headers["__published_at__"] = time.time()

    def on_after_task_publish(self, sender, **_kwargs):
        TASK_PUBLISHED.labels(task=sender).inc()

    def on_task_prerun(self, task, **_kwargs):
        TASK_PRERUN.labels(task=task.name).inc()
        published_at = task.request.get("__published_at__")
        if published_at is not None:
            queue_time = time.time() - published_at
            TASK_QUEUE_TIME.labels(task=task.name).observe(queue_time)
        task.request.__started_at__ = time.monotonic()

    def on_task_postrun(self, task, state, **_kwargs):
        TASK_POSTRUN.labels(task=task.name, state=state).inc()
        started_at = task.request.get("__started_at__")
        if started_at is not None:
            execution_time = time.monotonic() - started_at
            TASK_EXECUTION_TIME.labels(task=task.name).observe(execution_time)
