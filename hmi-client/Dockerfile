FROM python:3.11-slim
RUN pip install pymodbus
WORKDIR /app
COPY hmi_dashboard.py .
CMD ["tail", "-f", "/dev/null"]
