FROM python:alpine
ARG MNAMER_VERSION=2.4.2
ARG UID=1000
ARG GID=1000
RUN adduser mnamer --disabled-password
USER mnamer
RUN pip3 install --no-cache-dir --upgrade pip mnamer==${MNAMER_VERSION}
ENTRYPOINT ["python", "-m", "mnamer"]
CMD ["--batch", "/mnt"]
