FROM python:3.14-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN DJANGO_SECRET_KEY=build uv run --no-dev manage.py collectstatic --noinput
EXPOSE 8080
CMD ["uv", "run", "--no-dev", "gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8080", "--workers", "2"]
