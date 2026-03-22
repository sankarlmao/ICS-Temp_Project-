FROM python:3.11-slim
RUN apt-get update && apt-get install -y nmap curl iputils-ping openssh-client procps sudo
RUN pip install pymodbus
WORKDIR /app
COPY setup_users.py .
COPY attack.py .
RUN python setup_users.py
CMD ["tail", "-f", "/dev/null"]
