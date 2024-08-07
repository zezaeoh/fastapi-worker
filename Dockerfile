FROM python:3.11 as builder

# Install Poetgry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./

ARG APP_ENV=prod
ENV PYTHONUNBUFFERED=1 APP_ENV=${APP_ENV}

RUN bash -c "if [ ${APP_ENV} == 'prod' ] ; then poetry install --no-root --only main ; else poetry install --no-root ; fi"

WORKDIR /app
ENTRYPOINT ["/app/bin/docker-entrypoint"]

FROM python:3.11-slim as app

LABEL maintainer="zezaeoh <zezaeoh@gmail.com>"

RUN ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime
RUN chmod 777 /tmp
RUN apt-get update && apt-get install -y --no-install-recommends \
        locales rdate openssl ca-certificates \
    && localedef -f UTF-8 -i ko_KR ko_KR.UTF-8 \
    && rm -rf /var/lib/apt/lists/*

ARG APP_ENV=prod
ENV LANG="ko_KR.UTF-8" LANGUAGE="ko_KR.UTF-8" LC_ALL="ko_KR.UTF-8" \
    PYTHONUNBUFFERED=1 APP_ENV=${APP_ENV} APP_PORT="8000"

WORKDIR /app

COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages

COPY . .

ENTRYPOINT ["/app/bin/docker-entrypoint"]