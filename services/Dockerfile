# 全6サービス共通のDockerfile。
# ビルドコンテキストはリポジトリのルート。SERVICE ビルド引数でサービスを切り替える。
# 例: docker build -f services/Dockerfile --build-arg SERVICE=product -t insurance-product .
FROM python:3.13-slim

ARG SERVICE
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    SERVICE_NAME=${SERVICE}

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 共通モジュールと対象サービスのアプリケーションコードをコピー
COPY common ./common
COPY services/${SERVICE}/app ./app

# シードデータをコピー(simulationは永続データを持たないため任意)
COPY data/seed ./data/seed
ENV SEED_FILE=/app/data/seed/${SERVICE}.json

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
