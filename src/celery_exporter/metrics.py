import prometheus_client  # type: ignore


TASK_PRERUN = prometheus_client.Counter(
    "celery_task_prerun_count_total", "Count of tasks started", ["task"]
)
TASK_POSTRUN = prometheus_client.Counter(
    "celery_task_postrun_count_total",
    "Count of tasks completed",
    ["task", "state"],
)
TASK_PUBLISHED = prometheus_client.Counter(
    "celery_task_published_count_total", "Count of tasks published", ["task"]
)
TASK_QUEUE_TIME = prometheus_client.Histogram(
    "celery_task_queue_time", "Time tasks spent in the queue", ["task"]
)
TASK_EXECUTION_TIME = prometheus_client.Histogram(
    "celery_task_execution_time", "Time tasks spent running", ["task"]
)
