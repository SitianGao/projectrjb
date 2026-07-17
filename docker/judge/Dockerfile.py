FROM python:3.11-slim-bookworm
RUN apt-get update && apt-get install -y --no-install-recommends \
    time && \
    rm -rf /var/lib/apt/lists/*
COPY judge.sh /judge.sh
RUN chmod +x /judge.sh && useradd -m runner
USER runner
WORKDIR /work
ENTRYPOINT ["/bin/bash", "/judge.sh"]
