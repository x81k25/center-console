FROM python:3.11-slim
WORKDIR /app
# Copy dependency files
COPY pyproject.toml uv.lock ./
# Install uv and dependencies (no project install - this is a Streamlit app, not a package)
RUN pip install uv && uv sync --frozen --no-install-project
# Copy application code
COPY . .
EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501", "--server.fileWatcherType=none"]