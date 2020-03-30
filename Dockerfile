FROM alpine:3.10 as builder
RUN apk add --update python3 python3-dev gcc musl-dev linux-headers jq libffi-dev openssl-dev
COPY Pipfile.lock /root/
RUN mkdir /root/wheel/ && jq --raw-output \
    '.default | to_entries[] | .key + .value.version + (.value.hashes | map(" --hash=\(.)") | join(""))' \
    /root/Pipfile.lock | awk '{print $1}' > /root/wheel/requirements.txt && ln -s /usr/bin/pip3 \
    /usr/bin/pip && pip install wheel && pip wheel --wheel-dir=/root/wheel -r \
    /root/wheel/requirements.txt uwsgi

FROM alpine:3.10 as production
COPY --from=builder /root/wheel /wheel
RUN apk add python3 && ln -s /usr/bin/pip3 /usr/bin/pip && pip install \
    --no-index --find-links=/wheel -r \
    /wheel/requirements.txt uwsgi && rm -rf /wheel/ && addgroup -g 1000 \
 -S non-root && adduser -u 1000 -S non-root -G non-root

COPY wsgi.py /opt/code/
COPY project /opt/code/project/

RUN chown -R non-root.non-root /opt/code/
WORKDIR /opt/code/

ENTRYPOINT [ \
    "uwsgi", "--socket", "/tmp/uwsgi.sock", "--module", "wsgi", \
    "--master", "--processes", "4", "--threads", "2", "--uid",  \
    "non-root", "--gid", "non-root" \
]
