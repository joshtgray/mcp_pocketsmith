FROM python:3.12-slim

WORKDIR /app

# Install dependencies first for better layer caching
COPY pyproject.toml README.md ./
COPY src/ src/
RUN pip install --no-cache-dir .

# Create non-root user
RUN useradd --create-home --shell /bin/bash mcp
USER mcp

# Transport configuration
ENV MCP_TRANSPORT=sse
ENV MCP_HOST=0.0.0.0
ENV MCP_PORT=3401

EXPOSE 3401

CMD ["python", "-m", "pocketsmith_mcp"]
