FROM python:alpine
ARG MNAMER_VERSION=2.4.1
RUN pip3 install --no-cache-dir --upgrade pip mnamer==${MNAMER_VERSION}
ENTRYPOINT ["mnamer"]
CMD ["--batch", "/mnt"]