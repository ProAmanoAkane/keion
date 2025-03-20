FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install -y ffmpeg
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY src .
CMD [ "python", "-uO", "main.py"]