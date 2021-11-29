FROM python:3.10

WORKDIR /app

COPY requirements.txt .
ENV PATH=/venv/bin:$PATH
RUN : \
    && python3 -m venv /venv \
    && pip install -r requirements.txt

COPY . .
