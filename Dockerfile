FROM debian:stable-slim as builder
RUN apt update && apt install -y python3 python3-dev python3-pip gcc jq
COPY Pipfile.lock /root/
RUN mkdir /root/wheel/ && jq --raw-output \
    '.default | to_entries[] | .key + .value.version + (.value.hashes | map(" --hash=\(.)") | join(""))' \
    /root/Pipfile.lock | awk '{print $1}' > /root/wheel/requirements.txt && ln -s /usr/bin/pip3 \
    /usr/bin/pip && pip install wheel && pip wheel --wheel-dir=/root/wheel -r \
    /root/wheel/requirements.txt uwsgi

FROM debian:stable-slim as production
COPY --from=builder /root/wheel /wheel
RUN apt update && apt install -y python3 python3-pip && ln -s /usr/bin/pip3 /usr/bin/pip && pip install \
    --no-index --find-links=/wheel -r \
    /wheel/requirements.txt uwsgi && rm -rf /wheel/ && adduser --group --system non-root
ENV PATH="/usr/local/bin:${PATH}"

COPY wsgi.py /opt/code/
COPY project /opt/code/project/

RUN chown -R non-root.non-root /opt/code/
WORKDIR /opt/code/

ENTRYPOINT [ \
   "uwsgi", "--socket", "/tmp/uwsgi.sock", "--module", "wsgi", \
   "--master", "--processes", "4", "--threads", "2", "--uid",  \
   "non-root", "--gid", "non-root" \
]
