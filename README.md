# Celery-Local-Exporter

A Prometheus metrics exporter for Celery which lives directly in the celery processes. Unlike other Celery exporters, this does not require use of the events system or a result backend.

## Quick Start

To install:

```
pip install celery-local-exporter
```

To set up the exporter, in your celeryconfig.py or other settings file:

```
from celery_exporter import CeleryExporter
CeleryExporter.install()
```

The `prefork` concurrency pool is not supported at this time, I recommend using `-P threads`.
