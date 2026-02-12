# Use the local base image we created
FROM macro-engine-base:latest

WORKDIR /home/spark

# Copy the real Excel file and 'rename' it to library.xlsx internally
COPY external_data/GBweb_Row_Format.xlsx ./library.xlsx
COPY external_data/longdata.csv ./external_data/longdata.csv

# Copy only the files that change frequently
COPY src/ ./src/
COPY library.xlsx .
COPY models/ ./models/

# The command to run your diagnostic engine
CMD ["python3", "src/engine.py"]