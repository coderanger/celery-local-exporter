import os
import os.path
import subprocess
import sys
import time

import pytest
import requests


@pytest.fixture
def launch_worker(tmp_path_factory):
    procs = []

    def _inner(pool="threads", *args):
        if procs:
            raise ValueError("already started")
        os.environ["DATA_FOLDER_IN"] = str(tmp_path_factory.mktemp("data_in"))
        os.environ["DATA_FOLDER_OUT"] = str(
            tmp_path_factory.mktemp("data_out")
        )
        os.environ["RESULTS"] = str(tmp_path_factory.mktemp("results"))
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "celery",
                "-A",
                "app1",
                "worker",
                "-l",
                "debug",
                "-P",
                pool,
            ]
            + list(args),
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        procs.append(proc)
        # Wait a second to let it start up.
        time.sleep(1)
        # For future calls to run(), set them up to deliver to the inbox.
        os.environ["DATA_FOLDER_OUT"] = os.environ["DATA_FOLDER_IN"]
        return proc

    yield _inner

    for proc in procs:
        proc.terminate()
        proc.wait()
        out, err = proc.communicate()
        print(out.decode())
        print(err.decode())
        proc.stdout.close()
        proc.stderr.close()


@pytest.fixture
def run():
    def _inner(code):
        read, write = os.pipe()
        os.write(write, code.encode())
        os.close(write)
        return subprocess.check_call(
            [sys.executable],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdin=read,
        )

    return _inner


def test_starting(launch_worker):
    w = launch_worker()
    assert w.poll() is None
    r = requests.get("http://localhost:9000/")
    assert "celery_task_execution_time" in r.text


def test_run_task_add(launch_worker, run):
    w = launch_worker()
    assert w.poll() is None
    run(
        """
import app1
app1.add.delay(1, 1).wait(60)
    """
    )
    r = requests.get("http://localhost:9000/")
    assert (
        'celery_task_postrun_count_total{state="SUCCESS",task="app1.add"} 1.0'
        in r.text
    )


def test_run_task_add_twice(launch_worker, run):
    w = launch_worker()
    assert w.poll() is None
    run(
        """
import app1
x = app1.add.delay(1, 1)
y = app1.add.delay(1, 2)
x.wait(60)
y.wait(60)
    """
    )
    r = requests.get("http://localhost:9000/")
    assert (
        'celery_task_postrun_count_total{state="SUCCESS",task="app1.add"} 2.0'
        in r.text
    )


def test_run_task_sleep(launch_worker, run):
    w = launch_worker()
    assert w.poll() is None
    run(
        """
import app1
app1.sleep.delay(5).wait(60)
    """
    )
    r = requests.get("http://localhost:9000/")
    assert (
        'celery_task_postrun_count_total{state="SUCCESS",task="app1.sleep"} 1.0'
        in r.text
    )
    assert (
        'celery_task_execution_time_bucket{le="5.0",task="app1.sleep"} 0.0'
        in r.text
    )
    assert (
        'celery_task_execution_time_bucket{le="7.5",task="app1.sleep"} 1.0'
        in r.text
    )
