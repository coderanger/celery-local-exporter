import os
import time

from celery import Celery

from celery_exporter import CeleryExporter


app = Celery("tasks", broker="filesystem://")
app.conf.broker_transport_options = {
    "data_folder_in": os.environ["DATA_FOLDER_IN"],
    "data_folder_out": os.environ["DATA_FOLDER_OUT"],
}
app.conf.result_backend = "file://" + os.environ["RESULTS"]


CeleryExporter.install()


@app.task
def add(x, y):
    return x + y


@app.task
def sleep(n):
    time.sleep(n)
