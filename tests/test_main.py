import unittest.mock
import project.app
import os


class TestAlertmanagerActions(unittest.TestCase):
    def setUp(self):
        microservice_patch = unittest.mock.patch("project.app.Microservice")
        self.microservice = microservice_patch.start()

    def tearDown(self):
        self.microservice.stop()

    @unittest.mock.patch("sys.exit")
    def test_read_config_ok(self, exit_calls):
        os.environ["ALERTMANAGER_ACTIONS_CONFIG"] = "tests/config-ok.yml"
        alertmanager_actions = project.app.AlertmanagerActions()
        data = [
            {
                "labels": {"alertname": "TestActions", "test": "yes"},
                "command": "hostname",
            }
        ]
        assert data == alertmanager_actions.config
        assert exit_calls.call_count == 0

    @unittest.mock.patch("sys.exit")
    def test_read_config_ko(self, exit_calls):
        os.environ["ALERTMANAGER_ACTIONS_CONFIG"] = "tests/config-ko.yml"
        alertmanager_actions = project.app.AlertmanagerActions()
        data = [{"labels": {"alertname": "TestActions", "test": "yes"}}]
        assert data == alertmanager_actions.config
        assert exit_calls.call_count == 1

    @unittest.mock.patch("project.app.request")
    @unittest.mock.patch("subprocess.Popen")
    def test_launch_action_local_ok(self, popen, request):
        os.environ["ALERTMANAGER_ACTIONS_CONFIG"] = "tests/config-ok.yml"
        request.content_type = "application/json"
        request.json = {
            "receiver": "alertmanager-actions",
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "TestActions",
                        "environment": "pro",
                        "prometheus": "monitoring/kube-prometheus",
                        "test": "yes",
                    },
                    "annotations": {"description": "Alerta de prueba."},
                    "startsAt": "2020-04-16T10:09:23.893006315Z",
                    "endsAt": "2020-04-16T14:07:53.893006315Z",
                    "generatorURL": "http://prom.es/graph?g0.expr=1",
                }
            ],
            "groupLabels": {"alertname": "TestActions"},
            "commonLabels": {
                "alertname": "TestActions",
                "environment": "pro",
                "prometheus": "monitoring/kube-prometheus",
                "test": "yes",
            },
            "commonAnnotations": {"description": "Alerta de prueba."},
            "externalURL": "http://alerts.es",
            "version": "4",
            "groupKey": '{}/{test="yes"}:{alertname="TestActions"}',
        }
        popen.return_value.communicate.return_value = (b"equilibry", None)
        alertmanager_actions = project.app.AlertmanagerActions()
        action = alertmanager_actions._launch_action()
        assert action == "OK"
        assert popen.call_count == 1

    @unittest.mock.patch("project.app.request")
    @unittest.mock.patch("subprocess.Popen")
    def test_launch_action_local_ko(self, popen, request):
        os.environ["ALERTMANAGER_ACTIONS_CONFIG"] = "tests/config-ok.yml"
        request.content_type = ""
        request.json = {
            "receiver": "alertmanager-actions",
            "status": "firing",
            "alerts": [
                {
                    "status": "firing",
                    "labels": {
                        "alertname": "TestActions",
                        "environment": "pro",
                        "prometheus": "monitoring/kube-prometheus",
                        "test": "yes",
                    },
                    "annotations": {"description": "Alerta de prueba."},
                    "startsAt": "2020-04-16T10:09:23.893006315Z",
                    "endsAt": "2020-04-16T14:07:53.893006315Z",
                    "generatorURL": "http://prom.es/graph?g0.expr=1",
                }
            ],
            "groupLabels": {"alertname": "TestActions"},
            "commonLabels": {
                "alertname": "TestActions",
                "environment": "pro",
                "prometheus": "monitoring/kube-prometheus",
                "test": "yes",
            },
            "commonAnnotations": {"description": "Alerta de prueba."},
            "externalURL": "http://alerts.es",
            "version": "4",
            "groupKey": '{}/{test="yes"}:{alertname="TestActions"}',
        }
        popen.return_value.communicate.return_value = (b"equilibry", None)
        alertmanager_actions = project.app.AlertmanagerActions()
        action = alertmanager_actions._launch_action()
        assert action == "KO"
        assert popen.call_count == 0
