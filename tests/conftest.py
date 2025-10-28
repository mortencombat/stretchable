import logging

import pytest


def pytest_configure(config):
    logger = logging.getLogger("stretchable")
    logger.setLevel(logging.INFO)
    logFormatter = logging.Formatter("%(levelname)s:%(name)s:%(message)s")
    fileHandler = logging.FileHandler("debug.log")
    fileHandler.setFormatter(logFormatter)
    logger.addHandler(fileHandler)


def pytest_collection_modifyitems(config, items):
    """Run all smoke tests first."""
    critical = [i for i in items if "critical" in i.keywords]
    rest = [i for i in items if "critical" not in i.keywords]
    items[:] = critical + rest


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    # Let pytest generate the report first
    outcome = yield
    report = outcome.get_result()

    if report.when == "call" and report.failed:
        if any(mark.name == "critical" for mark in item.own_markers):
            pytest.exit(f"Stopping: critical test failed ({item.nodeid})")
