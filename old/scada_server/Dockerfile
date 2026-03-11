FROM python:3.9-slim
WORKDIR /app
COPY server.py /app/server.py
RUN pip install flask
EXPOSE 8080
CMD ["python", "server.py"]
