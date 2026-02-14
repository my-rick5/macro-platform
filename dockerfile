FROM macro-engine-base:latest

WORKDIR /home/app

# Copy your local project files
COPY . .

# Explicitly set the Python Path to include the current directory
ENV PYTHONPATH="/home/app"

# Pre-create the result folders so 'docker cp' never fails again
RUN mkdir -p results external_data

# The fix: Ensure the engine runs from the directory where it can see 'pyfrbus'
CMD ["python3", "src/engine.py"]