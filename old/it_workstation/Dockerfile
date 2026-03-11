FROM alpine:latest
RUN apk add --no-cache openssh nmap curl bash
RUN ssh-keygen -A
RUN adduser -D employee && echo "employee:password123" | chpasswd
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
