FROM python:3.12-slim-bookworm

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Install ffmpeg for audio conversion
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy

# Copy dependency files
COPY uv.lock pyproject.toml ./

# Install dependencies
RUN uv sync --locked --no-install-project --no-dev

# Copy the application code
COPY bot.py ./
COPY src/ ./src/

# Expose the port (Pipecat runner default)
EXPOSE 7860

# Run the bot - bind to 0.0.0.0 to allow external access
CMD ["uv", "run", "bot.py", "-t", "twilio", "--host", "0.0.0.0", "--port", "7860"]