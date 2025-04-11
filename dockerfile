 FROM alpine
 RUN apk add python3  py3-pip \ 
  && python3 -m pip install requests --break-system-packages
 COPY namecheap_ddns.py .
 CMD ["python3", "namecheap_ddns.py"]