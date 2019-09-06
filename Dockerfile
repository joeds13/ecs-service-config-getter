FROM python:3.7-alpine

COPY python/requirements.txt ./

RUN pip3 install \
        --trusted-host pypi.org \
        --no-cache-dir \
        -r requirements.txt

COPY app /app

ENTRYPOINT [ "python", "/app/app.py" ]
