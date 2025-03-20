# Stage 1: Builder
FROM python:3.13-slim AS builder

WORKDIR /app

# Copy poetry files
COPY poetry.lock pyproject.toml ./

# Install poetry and dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry && \
    poetry config virtualenvs.in-project true && \
    poetry install --no-root

# print list of installed packages to check if everything is installed
RUN /app/.venv/bin/pip freeze

# Stage 2: Application
FROM python:3.13-slim

RUN apt-get update && apt-get install --no-install-recommends -y \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

WORKDIR /app

# Copy virtual environment from builder stage
COPY --from=builder /app/.venv /app/.venv

# Copy application files
COPY src ./src
COPY entrypoint.sh ./

# Set up environment variables and add venv to PATH
ENV PATH="/app/.venv/bin:$PATH"

# Make entrypoint.sh executable
RUN chmod +x entrypoint.sh

# Set the entrypoint
ENTRYPOINT ["./entrypoint.sh"]

# Run the application
CMD ["python", "-uO", "src/main.py"]