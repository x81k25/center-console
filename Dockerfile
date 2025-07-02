FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install uv && uv pip install --system -r requirements.txt
COPY . .
ENV CENTER_CONSOLE_PORT_EXTERNAL=8501
EXPOSE ${CENTER_CONSOLE_PORT_EXTERNAL}
CMD ["sh", "-c", "streamlit run app.py --server.address=0.0.0.0 --server.port=${CENTER_CONSOLE_PORT_EXTERNAL}"]