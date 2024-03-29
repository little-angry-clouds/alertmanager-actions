#!/usr/bin/env python

import subprocess  # nosec
import sys
from os import environ
from threading import Timer

import yaml
from flask import jsonify, request
from pyms.flask.app import Microservice
from prometheus_client import Counter


class AlertmanagerActions:
    def __init__(self):
        """
        Initialize the flask endpoint and launch the function that will throw
        the threads that will update the metrics.
        """
        self.lock = {}
        self.app = Microservice().create_app()
        self.logger = self.app.logger
        self.read_config()
        self.serve_endpoints()

    def read_config(self):
        """
        Read configuration from yaml file.
        """
        if "ALERTMANAGER_ACTIONS_CONFIG" in environ:
            path = environ["ALERTMANAGER_ACTIONS_CONFIG"]
        else:
            path = "config.yml"  # pragma: no cover
        log = "Reading configuration file in path: %s" % (path)
        self.logger.debug(log)
        config = []
        try:
            config = yaml.safe_load(open(path))["alertmanager_actions"]
        except Exception as error:
            log = "There was an error loading the file: %s" % (error)
            self.logger.error(log)
            sys.exit(1)

        for action in config:
            main_keys = ["labels", "command"]
            differences = list(set(main_keys) - set(action))
            if differences:
                log = "There's configuration missing. Add the next keys: [%s]"
                log = log % (", ".join(differences))
                self.logger.error(log)
                sys.exit(1)

        # Initialize locks and metrics and clean the locks
        for action in config:
            self.lock[action["name"]] = False
            # Reinitializing the same metric fails, so catch that error
            try:
                self.counter = Counter(
                    "alertmanager_actions_executions",
                    "Number of alertmanager actions executions",
                    ["action", "state", *action["labels"].keys()],
                )
            except ValueError:
                pass

        log = "Configuration read: %s" % (config)
        self.logger.debug(log)
        self.config = config

    def launch_action(self):
        treated_actions = []
        if not request.content_type:
            self.logger.warning(
                "The received content type should be 'application/json'."
            )
        valid = self._check_valid_request(request)
        if not valid:
            return "KO"
        self.logger.debug("Received request: %s" % request.json)
        received_labels = [x["labels"] for x in request.json["alerts"]]
        for action in self.config:
            self.logger.debug("Action: %s" % action)
            labels = action["labels"]
            for received_label in received_labels:
                self.logger.debug("Received label: %s" % received_label)
                # Proceed only if action's labels are in received labels
                if received_label.items() >= labels.items():
                    try:
                        locked = self._lock_action(action["name"])
                        if locked:
                            return "KO"
                        treated_actions, treated = self._treat_action(
                            action["name"], treated_actions
                        )
                        if treated:
                            self._unlock_action(action["name"])
                            return "KO"
                        if "timeout" in action:
                            timeout = action["timeout"]
                        else:
                            # Default is five minutes
                            timeout = 180
                        self._execute_command(
                            action["command"],
                            received_label.items(),
                            labels.items(),
                            action["name"],
                            timeout,
                        )
                        self._unlock_action(action["name"])
                    except Exception as err:
                        self.logger.error("Error: %s" % err)
                        self._unlock_action(action["name"])
        return "OK"

    def _execute_command(self, command, received_labels, config_labels, action_name, timeout):
        # Make available all labels through environmental variables
        env = environ.copy()
        for k, v in received_labels:
            env[k.upper()] = v
        # Join the list of commands to one line with a ; separator
        cmd = ";".join([x for x in command])
        self.logger.debug("Command: %s" % cmd)
        # Timeout for command
        kill = lambda process: process.kill()
        # TODO The command is executed in a very untrustful way
        command = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,  # nosec
            env=env,
        )
        my_timer = Timer(timeout, kill, [command])
        # Treat command output with timeout
        try:
            my_timer.start()
            stdout, stderr = command.communicate()
        finally:
            my_timer.cancel()
        self.logger.debug("Command output: %s" % stdout.decode(encoding="UTF-8"))
        if stderr:
            self.logger.error("Error: %s" % stderr)
        return_code = command.returncode
        # Only contemplate correct or incorrect executions
        if return_code != 0:
            return_code = 1

        labels_values = [v for k, v in config_labels]
        self.counter.labels(action_name, return_code, *labels_values).inc()

    def _treat_action(self, action_name, treated_actions):
        # Proceed only if the action hasn't been treated in the same request
        # AKA alerts deduplication
        if action_name in treated_actions:
            self.logger.debug(
                "Action already treated, so the command won't be executed"
            )
            return treated_actions, True
        treated_actions.append(action_name)
        return treated_actions, False

    def _lock_action(self, action_name):
        # This prevents the action to be executed if shortly after receiving
        # the alert but before executing, the same action is received
        if self.lock[action_name]:
            self.logger.debug(
                "The lock for '%s' is active, so the command won't be executed"
                % action_name
            )
            return True
        self.lock[action_name] = True
        self.logger.debug("The lock for '%s' is activated" % action_name)
        return False

    def _unlock_action(self, action_name):
        self.lock[action_name] = False
        self.logger.debug("The lock for '%s' is deactivated" % action_name)

    def _check_valid_request(self, request):
        if "alerts" not in request.json:
            self.logger.debug("Invalid request: %s" % request.json)
            return False
        if type(request.json["alerts"]) is not list:
            self.logger.debug("Invalid request: %s" % request.json)
            return False
        return True

    def serve_endpoints(self):
        """
        Main method to serve the metrics. It's used mainly to get the self
        parameter and pass it to the next function.
        """

        @self.app.route("/", methods=["POST"])
        def root():
            """
            Exposes a blank html page with a link to the metrics.
            """
            state = self.launch_action()
            return jsonify(message=state)

        @self.app.route("/-/reload")
        def reload():
            """
            Stops the threads and restarts them.
            """
            self.logger.info("Reloading configuration")
            self.read_config()
            self.logger.info("Configuration reloaded")
            return jsonify(message="OK")

    def run_webserver(self):
        "Start the web application."
        self.app.run(port="8080", host="0.0.0.0", use_reloader=False)  # nosec
