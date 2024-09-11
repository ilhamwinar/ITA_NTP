FROM python:3.9-slim-bullseye
RUN python -m pip install --upgrade pip
RUN pip install fastapi
RUN pip install uvicorn
RUN pip install python-multipart
RUN pip install paramiko

ENV TZ=Asia/Jakarta


EXPOSE 8300:8300

COPY api_add_cctv.py /api_add_cctv.py
COPY myscript.sh /myscript.sh
COPY reboot.sh /reboot.sh

WORKDIR ./Music
CMD ["python3","api_add_cctv.py"]


