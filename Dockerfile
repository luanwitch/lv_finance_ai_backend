FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Chave apenas para comandos executados DURANTE o build
# (collectstatic). O valor real vem das variáveis de ambiente do Render
# em runtime, que têm precedência sobre o ENV da imagem.
ENV DJANGO_SECRET_KEY="docker-build-only-dummy-secret-key"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN python manage.py collectstatic --noinput

EXPOSE 8000

# Aplica migrações pendentes antes de subir o servidor — garante que o
# schema do banco acompanhe o código em cada deploy (idempotente).
# "exec" promove o gunicorn a processo principal (PID 1) para receber
# sinais corretamente.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn config.wsgi:application -c gunicorn.conf.py"]
