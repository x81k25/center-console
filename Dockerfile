FROM python:3.11-slim
WORKDIR /app
# Copy dependency files
COPY pyproject.toml uv.lock* ./
# Install dependencies
RUN pip install uv && uv sync --frozen --no-install-project
# Copy application code
COPY . .
# Install the project itself
RUN uv sync --frozen
EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.fileWatcherType=none"]