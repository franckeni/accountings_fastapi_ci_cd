FROM python:3.12-slim AS build

ARG CURRENT_USER

# Set environment variables 
ENV PYTHONDONTWRITEBYTECODE 1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=100 PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml poetry.lock ./

RUN pip install "poetry==1.8.2" \
    && poetry config virtualenvs.in-project true \
    && poetry install --no-root --no-ansi --no-interaction \
    && poetry export -f requirements.txt -o requirements.txt 


### Final stage
FROM python:3.12-slim AS final

ARG CURRENT_USER

ENV APP_HOME=/home/app
WORKDIR $APP_HOME

COPY --from=build /app/requirements.txt $APP_HOME/
COPY ./.env.temp ./entrypoint.sh $APP_HOME/

RUN set -ex \
    && groupadd -r "$CURRENT_USER" \
    && useradd --no-log-init -r -g "$CURRENT_USER" "$CURRENT_USER" \
    && apt-get update -y\
    && apt-get upgrade -y \
    && apt-get --no-install-recommends install -y curl gettext-base \
    && pip install -r "$APP_HOME"/requirements.txt \
    && apt-get autoremove -y \
    && apt-get clean -y \
    && rm -rf /var/lib/apt/lists/* \
    && chmod +x "$APP_HOME"/entrypoint.sh

COPY ./src $APP_HOME

RUN chown -R "$CURRENT_USER":www-data .

# For Ci / CD pipeline env variables
ENTRYPOINT ["./entrypoint.sh"]

EXPOSE 8080

# Set the default user
USER $CURRENT_USER