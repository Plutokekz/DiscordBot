FROM python:3.11-slim

RUN apt update
RUN apt install -y build-essential ffmpeg curl
RUN pip install poetry

WORKDIR /

COPY pyproject.toml ./

RUN poetry install --no-root
COPY bot ./bot

CMD ["poetry", "run", "python", "-m", "bot.main"]