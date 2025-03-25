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

COPY ./poetry.lock /usr/src/fastapi/poetry.lock
COPY ./pyproject.toml /usr/src/fastapi/pyproject.toml

WORKDIR /usr/src/fastapi

RUN poetry config virtualenvs.create false
RUN poetry install --no-root --only main

COPY ./src /usr/src/fastapi
COPY ./commands /commands

RUN find /commands -type f -name "*.sh" -exec dos2unix {} + && chmod +x /commands/*.sh || true

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/usr/src/fastapi"]
