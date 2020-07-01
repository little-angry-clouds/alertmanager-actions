# Alertmanager Actions

![Test](https://github.com/little-angry-clouds/alertmanager-actions/workflows/Test%20and%20build%20docker/badge.svg)
[![Coverage
Status](https://coveralls.io/repos/github/little-angry-clouds/alertmanager-actions/badge.svg?branch=master)](https://coveralls.io/github/little-angry-clouds/alertmanager-actions?branch=master)
[![Total
alerts](https://img.shields.io/lgtm/alerts/g/little-angry-clouds/alertmanager-actions.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/little-angry-clouds/alertmanager-actions/alerts/)
[![Language grade:
Python](https://img.shields.io/lgtm/grade/python/g/little-angry-clouds/alertmanager-actions.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/little-angry-clouds/alertmanager-actions/context:python)

An Alert Manager
[receiver](https://prometheus.io/docs/alerting/configuration/#receiver) that
executes arbitrary commands when receiving alerts.

It's dead simple. You associate alert labels to an action, and it will execute
the action.

## Configuration
This program uses [pyms](https://github.com/python-microservices/pyms), the cool
library to create REST python microservices. The configuration section under
`pyms` is for that. The one under `alertmanager_actions` is the section for the
program per se:

``` yaml
pyms:
  services:
    metrics: true
  config:
    debug: false
    app_name: alertmanager-actions
    testing: false
alertmanager_actions:
  - labels:
      alertname: IpsecStatus
      action: restart
    command: hostname
```

You may use this to execute commands over ssh, like this:

``` yaml
pyms:
  services:
    metrics: true
  config:
    debug: false
    app_name: alertmanager-actions
    testing: false
alertmanager_actions:
  - labels:
      alertname: ExampleAlertName
      action: restart
    command: ssh -i /home/user/.ssh/id_rsa user@mycoolbox.com hostname
```

It's possible to read a more complete step by step documentation
[here](./docs/configuration.md).

Also, there's a docker image you may use in [Docker
Hub](https://hub.docker.com/repository/docker/littleangryclouds/alertmanager-actions).

## Metrics
It exposes some prometheus metrics. The ones that come with
[Pyms](https://py-ms.readthedocs.io/en/latest/services/#metrics)
and then ones about the Alertmanager Actions itself. The created metric would be
something like this:

``` text
# HELP alertmanager_actions_total Number of alertmanager actions executions
# TYPE alertmanager_actions_total counter
alertmanager_actions_total{action="TestActions",alertname="TestActions",state="0"} 1.0
alertmanager_actions_total{action="TestActions",alertname="TestActions",state="1"} 1.0
# HELP alertmanager_actions_created Number of alertmanager actions executions
# TYPE alertmanager_actions_created gauge
alertmanager_actions_created{action="TestActions",alertname="TestActions",state="0"} 1.5936252529745235e+09
alertmanager_actions_created{action="TestActions",alertname="TestActions",state="1"} 1.5936252952259927e+09
```

The metric's name is `alertmanager_actions_executions` and will have the next
metrics:
- action: The action name.
- state: The state of the executed command. 0 means that it worked correctly, 1
  that it didn't.
- arbitrary labels: There will also be added all the labels that are used to
  identify the action. Following the above example, the next labels will be
  added:
  - alertname: ExampleAlertName
  - action: restart

## Development
### Tests

``` bash
pipenv install
pipenv run pip freeze > requirements.txt
tox
```
