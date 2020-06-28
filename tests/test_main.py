import unittest.mock
import project.app
import os
import pytest


@pytest.mark.parametrize("case,number_exit_calls", [("ok", 0), ("ko", 1)])
@unittest.mock.patch("sys.exit")
def test_read_config(exit_calls, case, number_exit_calls):
    ms = unittest.mock.patch("project.app.Microservice").start()
    os.environ["ALERTMANAGER_ACTIONS_CONFIG"] = "tests/config-" + case + ".yml"
    project.app.AlertmanagerActions()
    assert exit_calls.call_count == number_exit_calls
    ms.stop()


@pytest.mark.parametrize(
    "test_name,labels,lock,command_executions,result",
    [
        ("all good", {"alertname": "TestActions", "test": "yes"}, False, 1, "OK"),
        ("lock active", {"alertname": "TestActions", "test": "yes"}, True, 0, "KO"),
    ],
)
@unittest.mock.patch("project.app.request")
@unittest.mock.patch("subprocess.Popen")
def test_launch_action_local(
    popen, request, test_name, labels, lock, command_executions, result
):
    ms = unittest.mock.patch("project.app.Microservice").start()
    os.environ["ALERTMANAGER_ACTIONS_CONFIG"] = "tests/config-ok.yml"

    data = EXAMPLE_JSON
    data["alerts"][0]["labels"] = labels

    request.json = data
    request.content_type = "application/json"
    popen.return_value.communicate.return_value = (b"equilibry", None)
    alertmanager_actions = project.app.AlertmanagerActions()
    alertmanager_actions.lock[labels["alertname"]] = lock
    action = alertmanager_actions._launch_action()
    assert action == result
    assert popen.call_count == command_executions
    ms.stop()


EXAMPLE_JSON = {
    "receiver": "alertmanager-actions",
    "status": "firing",
    "alerts": [
        {
            "status": "firing",
            "labels": {
                "environment": "pro",
                "prometheus": "monitoring/kube-prometheus",
            },
            "annotations": {"description": "Alerta de prueba."},
            "startsAt": "2020-04-16T10:09:23.893006315Z",
            "endsAt": "2020-04-16T14:07:53.893006315Z",
            "generatorURL": "http://prom.es/graph?g0.expr=1",
        }
    ],
    "commonLabels": {"prometheus": "monitoring/kube-prometheus"},
    "commonAnnotations": {"description": "Alerta de prueba."},
    "externalURL": "http://alerts.es",
    "version": "4",
    "groupKey": '{}/{test="yes"}:{alertname="TestActions"}',
}
