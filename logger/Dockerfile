FROM python:3.11-slim
RUN pip install flask
WORKDIR /app
COPY logger.py .
RUN touch /var/log/scada_lab.log && chmod 666 /var/log/scada_lab.log
CMD ["python", "logger.py"]
