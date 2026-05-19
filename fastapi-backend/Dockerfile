FROM astral/uv:python3.12-trixie
 
# Set the working directory in the container
WORKDIR /app
 
# Copy the pyproject.toml and uv.lock files
COPY pyproject.toml uv.lock ./
 
# Install the dependencies using uv sync
RUN uv sync
 
# Copy the application code
COPY . .

# Copy the vscode launch configuration
COPY ./.vscode /.vscode
 
# Start with gunicorn: 4 workers, debugpy on port 5678
CMD ["uv", "run", "python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "gunicorn", "main:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
