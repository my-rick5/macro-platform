# Use the local base image we created
FROM macro-engine-base:latest

WORKDIR /home/spark

# Copy only the files that change frequently
COPY src/ ./src/
COPY library.xlsx .
COPY models/ ./models/

# The command to run your diagnostic engine
CMD ["python3", "src/engine.py"]