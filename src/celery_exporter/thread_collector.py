from prometheus_client.core import GaugeMetricFamily  # type: ignore


class CeleryThreadPoolCollector:
    def __init__(self, pool):
        self.pool = pool
        # This only works up until Python 3.6.
        self.enable_idle_threads_metric = hasattr(
            self.pool._work_queue, "mutex"
        )

    def collect(self):
        max_threads = self.pool._max_workers
        cur_threads = len(self.pool._threads)
        work_queue_size = self.pool._work_queue.qsize()

        yield GaugeMetricFamily(
            "celery_threadpool_max_worker_count",
            "The maxiumum number of worker threads.",
            value=max_threads,
        )

        yield GaugeMetricFamily(
            "celery_threadpool_current_worker_count",
            "The current number of worker threads.",
            value=cur_threads,
        )

        yield GaugeMetricFamily(
            "celery_threadpool_pending_tasks_count",
            "The number of work items in the queue, not being run yet.",
            value=work_queue_size,
        )

        if self.enable_idle_threads_metric:
            # Number of threads sitting in work_queue.get(block=True)
            with self.pool._work_queue.mutex:
                idle_threads = len(self.pool._work_queue.not_empty._waiters)

            yield GaugeMetricFamily(
                "celery_threadpool_idle_worker_count",
                "The current number of idle worker threads.",
                value=idle_threads,
            )
