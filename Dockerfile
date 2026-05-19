# syntax=docker/dockerfile:1

FROM python:alpine AS builder

RUN apk add --no-cache git
WORKDIR /src
COPY . .
RUN pip wheel --no-cache-dir --wheel-dir /wheels .

FROM python:alpine
ARG UID=1000
ARG GID=1000
RUN addgroup mnamer -g "$GID"
RUN adduser mnamer -u "$UID" -G mnamer --disabled-password
COPY --from=builder /wheels/*.whl /tmp/
RUN pip3 install --no-cache-dir --upgrade pip /tmp/*.whl \
    && rm -f /tmp/*.whl
USER mnamer
ENTRYPOINT ["python", "-m", "mnamer"]
CMD ["--batch", "/mnt"]
