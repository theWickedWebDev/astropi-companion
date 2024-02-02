FROM python:3.12.0

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_CACHE_DIR='/var/cache/pypoetry' \
    POETRY_HOME='/usr/local' \
    POETRY_VERSION=1.7.1

RUN pip install "poetry==$POETRY_VERSION"

WORKDIR /app

COPY ./README.md .
COPY ./poetry.lock .
COPY ./pyproject.toml .

RUN poetry install --no-interaction --no-ansi

COPY ./src ./src
COPY ./sessions ./sessions
COPY prod.env ./prod.env

ENV ENV='prod'

EXPOSE 5000

# poetry run python -m src.app mock-camera
CMD ["poetry", "run", "python", "-m", "src.app"]
