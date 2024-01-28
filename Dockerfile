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

COPY ./README.md /home/pi/astropi-companion/
COPY ./poetry.lock /home/pi/astropi-companion/
COPY ./pyproject.toml /home/pi/astropi-companion/

WORKDIR /home/pi/astropi-companion/

RUN poetry install --no-interaction --no-ansi

COPY ./src .
COPY ./sessions .
COPY .env .

EXPOSE 5000

# poetry run python -m src.app mock-camera
CMD ["/usr/local/bin/poetry", "run", "python", "-m", "src.app"]
