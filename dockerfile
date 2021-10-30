 FROM alpine
 RUN apk add python3  py3-pip
 RUN python3 -m pip install requests
 COPY namecheap_update_ip.py .
 CMD ["python3", "namecheap_update_ip.py"]