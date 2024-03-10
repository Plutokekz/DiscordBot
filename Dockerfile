FROM python:3.11

RUN apt-get update
RUN DEBIAN_FRONTEND="noninteractive" apt-get install -y -qq build-essential ffmpeg curl
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH = "${PATH}:/root/.local/bin"

WORKDIR /

COPY poetry.lock ./
COPY pyproject.toml ./

RUN poetry install
COPY . .

CMD ["poetry", "run", "python", "main.py"]