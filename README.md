# Alertmanager Actions
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
      alertname: IpsecStatus
      action: restart
    command: ssh -i /home/user/.ssh/id_rsa user@mycoolbox.com hostname
```

## Development
### Tests

``` bash
pipenv install
pipenv run pip freeze > requirements.txt
tox
```
