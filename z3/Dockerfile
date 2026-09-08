# Use an official Python runtime as a parent image
FROM python:3.13-slim

# Set the working directory in the container
WORKDIR /app

RUN mkdir -p /app/out

# Install Z3 and FastAPI
RUN pip install z3-solver "fastapi[standard]"

# Copy the rest of the application code to the container
COPY . /app

# Expose the port that the application will run on
EXPOSE 8000

# Run the application
CMD ["fastapi", "run", "main.py"]