# Stage 1: Builder image to install dependencies
FROM python:3.12-slim as builder

ENV PYTHONUNBUFFERED 1
WORKDIR /app

# Install uv, our package manager
RUN pip install uv

# Copy files required to install dependencies.
# We copy the whole project to be able to install it as a package.
COPY . ./

# Install dependencies from uv.lock (if present) and the project itself.
RUN uv venv && uv sync
CMD exec uv run --no-sync uvicorn main:app --port 8080 --host 0.0.0.0
