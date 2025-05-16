FROM python:3.13

LABEL org.opencontainers.image.source=https://github.com/MarcoBuster/railway-opendata
LABEL org.opencontainers.image.description="Italian railway opendata scraper and analyzer"
LABEL org.opencontainers.image.licenses=GPL-2.0-or-later

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

VOLUME /app/data
ENV PYTHONHASHSEED=0

COPY . .

ENTRYPOINT ["python", "main.py"]
