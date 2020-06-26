#!/usr/bin/env python

import logging
import subprocess
import sys
from os import environ

import yaml
from flask import jsonify, request
from pyms.flask.app import Microservice
from pyms.constants import LOGGER_NAME


logger = logging.getLogger(LOGGER_NAME)


class AlertmanagerActions:
    def __init__(self):
        """
        Initialize the flask endpoint and launch the function that will throw
        the threads that will update the metrics.
        """
        self.lock = {}
        self.app = Microservice().create_app()
        self._read_config()
        self.serve_endpoints()

    def _read_config(self):
        """
        Read configuration from yaml file.
        """
        if "ALERTMANAGER_ACTIONS_CONFIG" in environ:
            path = environ["ALERTMANAGER_ACTIONS_CONFIG"]
        else:
            path = "config.yml"  # pragma: no cover
        log = "Reading configuration file in path: %s" % (path)
        logger.debug(log)
        try:
            config = yaml.safe_load(open(path))["alertmanager_actions"]
        except Exception as error:
            log = "There was an error loading the file" % (error)
            logger.error(log)
            return

        for action in config:
            main_keys = ["labels", "command"]
            differences = list(set(main_keys) - set(action))
            if differences:
                log = "There's configuration missing. Add the next keys: [%s]"
                log = log % (", ".join(differences))
                logger.error(log)
                sys.exit(1)

        for action in config:
            self.lock[action["name"]] = False

        log = "Configuration read: %s" % (config)
        logger.debug(log)
        self.config = config

    def _launch_action(self):
        treated_actions = []
        if not request.content_type:
            logger.warning("The received content type should be 'application/json'.")
        logger.debug("Received Json: %s" % request.json)
        received_labels = [x["labels"] for x in request.json["alerts"]]
        for action in self.config:
            logger.debug("Action: %s" % action)
            labels = action["labels"]
            for received_label in received_labels:
                logger.debug("Received label: %s" % received_label)
                if labels.items() <= received_label.items():
                    if action["name"] in treated_actions:
                        logger.debug("Action already treated, so the command won't be executed")
                        return "OK"
                    if self.lock[action["name"]]:
                        logger.debug("The lock is active, so the command won't be executed")
                        return "OK"
                    treated_actions.append(action["name"])
                    self.lock[action["name"]] = True
                    # Make available all labels through environmental variables
                    env = environ.copy()
                    for k, v in received_label.items():
                        env[k.upper()] = v
                    cmd = ";".join([x for x in action["command"]])
                    logger.debug("Command: %s" % cmd)
                    command = subprocess.Popen(
                        cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        shell=True,
                        env=env
                    )
                    stdout, stderr = command.communicate()
                    logger.debug("Command output: %s" % stdout.decode(encoding="UTF-8"))
                    if stderr:
                        logger.error("Error: %s" % stderr)
                    self.lock[action["name"]] = False
        return "OK"

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
            state = self._launch_action()
            return jsonify(state)

        @self.app.route("/-/reload")
        def reload():
            """
            Stops the threads and restarts them.
            """
            logger.info("Reloading configuration")
            self._read_config()
            logger.info("Configuration reloaded")
            return jsonify("OK")

    def run_webserver(self):
        "Start the web application."
        self.app.run(port="8080", host="0.0.0.0", use_reloader=False)
