FROM python:3.10-slim

ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /usr/src

RUN apt-get update \
    && apt-get install -y \
    gcc \
    netcat-traditional \
    && pip install "poetry~=2.1.1" \
    && poetry config virtualenvs.create false \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists

EXPOSE 8080
COPY poetry.lock pyproject.toml ./

RUN poetry install --only main;


# Setup entry point
COPY docker/entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/entrypoint.sh
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

COPY . .

RUN chmod -R 775 .
RUN chown -R 1000:root .
USER 1000

CMD gunicorn --bind 0.0.0.0:8080 wsgi
