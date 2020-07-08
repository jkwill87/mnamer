FROM python:alpine
ARG MNAMER_VERSION=2.*
RUN pip3 install --no-cache-dir --upgrade pip mnamer==${MNAMER_VERSION}
ENTRYPOINT mnamer
