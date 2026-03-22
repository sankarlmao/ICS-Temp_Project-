FROM python:3.11-slim
RUN pip install flask requests pymodbus
WORKDIR /app
COPY app.py .
COPY attack.py .
CMD ["python", "app.py"]
