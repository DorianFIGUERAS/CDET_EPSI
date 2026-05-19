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
 
# Start the Uvicorn server using uv run
CMD ["uv", "run", "python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
