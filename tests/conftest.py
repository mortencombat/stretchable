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


# module-level flag used to request stopping the session
_STOP_MSG = None


def pytest_runtest_setup(item):
    """
    Attach a property to the item so we can detect its 'critical' mark later via reports.
    Also check stop flag and exit early (this is the primary stop gate).
    """
    global _STOP_MSG
    if _STOP_MSG:
        pytest.exit(_STOP_MSG)

    # attach marker info so it is visible on the TestReport.user_properties
    if any(mark.name == "critical" for mark in item.iter_markers()):
        item.user_properties.append(("critical", True))


def pytest_runtest_logreport(report):
    """Called when a test report is produced. If a critical test failed, request stop."""
    global _STOP_MSG
    if (
        report.when == "call"
        and report.failed
        and dict(report.user_properties).get("critical", False)
    ):
        _STOP_MSG = f"Stopping: critical test failed ({report.nodeid})"
