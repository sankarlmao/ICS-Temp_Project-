FROM python:3.11-slim
RUN pip install pymodbus
WORKDIR /app
COPY server.py .
CMD ["python", "server.py"]
