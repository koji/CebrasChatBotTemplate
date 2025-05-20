FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -u 1000 streamlit

# Create necessary directories and set permissions
RUN mkdir -p /app/.streamlit && \
    chown -R streamlit:streamlit /app

# Switch to non-root user
USER streamlit

COPY --chown=streamlit:streamlit requirements.txt ./
COPY --chown=streamlit:streamlit src/ ./src/
COPY --chown=streamlit:streamlit .streamlit/ ./.streamlit/

RUN pip3 install --user -r requirements.txt

# Set environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false
ENV STREAMLIT_GLOBAL_DEVELOPMENT_MODE=false

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["python", "-m", "streamlit", "run", "src/streamlit_app.py"]
