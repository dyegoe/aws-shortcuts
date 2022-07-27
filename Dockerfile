FROM alpine:3.16.0

COPY requirements.txt /requirements.txt

RUN apk add --no-cache python3 py3-pip && \
  pip3 install -r /requirements.txt && \
  rm -f /requirements.txt && \
  rm -rf /var/cache/apk/*