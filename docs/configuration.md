# Configuration

Alertmanager Actions is an Alertmanager Receiver. The first step to use it would
be deploy it.

## Deploy Alertmanager Actions
### Kubernetes
There's a [helm
chart](https://github.com/little-angry-clouds/charts/tree/master/alertmanager-actions)
with some features. It has secrets and pre-installing tools support. Say you'd
want to ssh to a machine to restart an nginx service when the alert `NginxDown`
bumps. You'd define a `values.yml` like the next:

```yaml
preInstall:
  enabled: true
  value: |
    apt update; apt install -y openssh-client

secrets:
  enabled: true
  values:
  - key: ssh-key
    value: SGksIHlvdSBjdXJpb3VzIHBlcnNvbiA6KQ==

config:
  alertmanager_actions: |
    - name: RestartNginx
      labels:
        alertname: NginxDown
        action: restart
      command:
        - ssh -o StrictHostKeyChecking=no -i /secrets/ssh-key ec2-user@$PRIVATE_IP sudo systemctl restart nginx
```

There's some stuff going here. First of all, pre-installing stuff. There's to
ways of doing so, using a custom image with the Alertmanager or using the
`preInstall` feature. Using the feature is pretty easy, you just activate the
feature and then install what you need in the container. In the example, since
we want to ssh to a box and restart a service, we only will need `ssh`.

Next, the secrets. It's possible to define a list of secrets. The `value` must be
base64 encoded. The `key` will be the name of the file containing the secret.
All secrets are mounted in the cointanier in `/secrets/`. So, the defined secret
will be in a file in the container in `/secrets/ssh-key`.

The last part, the actions. In the example there's defined an action called
`NginxDown` that will be activated if an alert with the labels `alertname` with
value `NginxDown` and `action` with value `restart` are received. When received,
it will execute the command. The command is pretty plain, but it has something
special. The environmental variable `$PRIVATE_IP`. This is one of the strongest
features, all alert labels are passed as environmental variables to the command.
In the example, it's assumed that the triggered alert has one label called
`$PRIVATE_IP` that contains the IP that can be used to reach the service.

### Plain box
TBD

## Configure the Alertmanager
The only part explained will be the one related to the receivers configuration.
So the next pieces of code won't work as is, you'll need a working prometheus +
alertmanager installation.

In this section there will be explained how to configure the route and the
receiver. The first one will be the route:

```yaml
route:
  routes:
  - receiver: alertmanager-actions
    match:
      actions: 'true'
```

This means that all alerts that the Alertmanager receive with the label
`actions` with the value `true` will be redirected to the `alertmanager-actions`
receiver.

The receiver itself is a webhook, its configuration it's pretty simple:

```yaml
receivers:
- name: alertmanager-actions
  webhook_configs:
  - send_resolved: false
    url: "http://alertmanager-actions/"
```

## Configure the alert
Again, the only part explained will be the one related to alert configuration.
So the next pieces of code won't work as is, you'll need a working prometheus +
alertmanager installation.

The next section is the configuration of an alert:

```yaml
groups:
- name: ipsec.rules
  rules:
  - alert: RestartNginx
    expr: nginx_down == 0
    labels:
      action: restart
    annotations:
      description: The proxy is down, will try to restart it automatically.
    for: 30s
```
