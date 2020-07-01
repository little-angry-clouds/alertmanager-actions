import unittest.mock
import project.app
import os
import pytest


@pytest.fixture()
def setup():
    ms = unittest.mock.patch("project.app.Microservice")
    ms.start()
    metrics = unittest.mock.patch("project.app.Counter")
    metrics.start()
    yield
    ms.stop()
    metrics.stop()


@pytest.mark.parametrize("case,number_exit_calls", [("ok", 0), ("ko", 1), ("nope", 1)])
@unittest.mock.patch("sys.exit")
def test_read_config(exit_calls, case, number_exit_calls, setup):
    os.environ["ALERTMANAGER_ACTIONS_CONFIG"] = "tests/config-" + case + ".yml"
    project.app.AlertmanagerActions()
    assert exit_calls.call_count == number_exit_calls


@pytest.mark.parametrize(
    "test_name,alerts,lock,command_executions,result",
    [
        (
            "all good",
            {"alerts": [{"labels": {"alertname": "TestActions", "test": "yes"}}]},
            False,
            1,
            "OK",
        ),
        (
            "lock active",
            {"alerts": [{"labels": {"alertname": "TestActions", "test": "yes"}}]},
            True,
            0,
            "KO",
        ),
        ("request without alerts", {"example": "fail"}, False, 0, "KO"),
        (
            "request without labels as list",
            {"alerts": {"labels": {"alertname": "TestActions", "test": "yes"}}},
            False,
            0,
            "KO",
        ),
    ],
)
@unittest.mock.patch("project.app.request")
@unittest.mock.patch("subprocess.Popen")
def test_launch_action_local(
    popen, request, test_name, alerts, lock, command_executions, result, setup
):
    os.environ["ALERTMANAGER_ACTIONS_CONFIG"] = "tests/config-ok.yml"
    data = alerts
    request.json = data
    request.content_type = "application/json"
    popen.return_value.communicate.return_value = (b"equilibry", None)
    alertmanager_actions = project.app.AlertmanagerActions()
    alertmanager_actions.lock["TestActions"] = lock
    action = alertmanager_actions.launch_action()
    assert action == result
    assert popen.call_count == command_executions
