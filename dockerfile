FROM macro-engine-base:latest

WORKDIR /home/app

# Copy your local project files
COPY src/ ./src/
COPY models/ ./models/

# The fix: Ensure the engine runs from the directory where it can see 'pyfrbus'
CMD ["python3", "src/engine.py"]