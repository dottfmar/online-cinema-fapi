FROM python:3.13

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=off

RUN apt update && apt install -y \
    gcc \
    libpq-dev \
    netcat-openbsd \
    postgresql-client \
    dos2unix \
    && apt clean

RUN python -m pip install --upgrade pip && \
    pip install poetry

COPY ./poetry.lock /usr/src/poetry/poetry.lock
COPY ./pyproject.toml /usr/src/poetry/pyproject.toml

RUN poetry config virtualenvs.create false

WORKDIR /usr/src/poetry

RUN poetry install --no-root --only main

WORKDIR /usr/src/fastapi

COPY ./src .

COPY ./commands /commands

RUN find /commands -type f -name "*.sh" -exec dos2unix {} + && chmod +x /commands/*.sh || true

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/usr/src/fastapi"]
