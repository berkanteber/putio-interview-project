FROM python:3.10

WORKDIR /app
COPY requirements.txt .

ENV PATH=/venv/bin:$PATH
RUN : \
    && python3 -m venv /venv \
    && python3 -m pip install -r requirements.txt

COPY . .

EXPOSE 5500

ENTRYPOINT ["python"]
CMD ["app.py"]
