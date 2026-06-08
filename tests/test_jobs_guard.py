from app import jobs


def test_jobs_executor_is_bounded():
    assert jobs._MAX_WORKERS >= 1
    assert jobs._EXECUTOR._max_workers == jobs._MAX_WORKERS
