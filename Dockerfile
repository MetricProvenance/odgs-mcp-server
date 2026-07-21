FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir odgs-mcp-server
ENTRYPOINT ["odgs-mcp-server", "--transport", "stdio"]
